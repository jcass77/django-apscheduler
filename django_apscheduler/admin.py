import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from django.contrib import admin, messages
from django.db.models import Avg
from django.utils.timezone import now

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django_apscheduler import util
from django_apscheduler.views import exec_now


def execute_now(ma, r, qs):
    for item in qs:
        item.next_run_time = now()
        item.save()


execute_now.short_description = "Force tasks to execute right now"


@admin.register(DjangoJob)
class DjangoJobAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "next_run_time_sec", "average_duration"]

    # 实例化调度器
    scheduler = BackgroundScheduler()
    # 调度器使用DjangoJobStore()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    def get_queryset(self, request):
        self._durations = {
            item[0]: item[1]
            for item in DjangoJobExecution.objects.filter(
                status=DjangoJobExecution.SUCCESS,
                run_time__gte=now() - datetime.timedelta(days=2)
            ).values_list("job").annotate(duration=Avg("duration"))
        }
        return super(DjangoJobAdmin, self).get_queryset(request)

    def next_run_time_sec(self, obj):
        return util.localize(obj.next_run_time)

    def average_duration(self, obj):
        return self._durations.get(obj.id) or 0

    def exec_now(self, request, queryset):
        ids = request.POST.getlist('_selected_action')
        if len(ids) == 0:
            messages.add_message(request, messages.ERROR, '必须选择一个或多个任务')
            return
        for db_id in ids:
            exec_now(db_id)
        messages.add_message(request, messages.SUCCESS, '触发执行成功')

    exec_now.short_description = '立即执行'
    exec_now.confirm = '您确定要立即执行吗？'
    # icon，参考element-ui icon与https://fontawesome.com
    exec_now.icon = 'fas fa-audio-description'
    # 增加自定义按钮
    actions = ['exec_now']


@admin.register(DjangoJobExecution)
class DjangoJobExecutionAdmin(admin.ModelAdmin):
    list_display = ["id", "job_name", "html_status", "run_time_sec", "duration"]

    list_filter = ["job__name", "run_time", "status"]

    def run_time_sec(self, obj):
        return util.localize(obj.run_time)

    def job_name(self, obj):
        return obj.job.name

    def get_queryset(self, request):
        return super(DjangoJobExecutionAdmin, self).get_queryset(
            request
        ).select_related("job")
