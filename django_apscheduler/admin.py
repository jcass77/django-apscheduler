import time
from datetime import timedelta

from apscheduler import events
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Avg
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django_apscheduler import util
from django_apscheduler.jobstores import DjangoJobStore, DjangoMemoryJobStore


@admin.register(DjangoJob)
class DjangoJobAdmin(admin.ModelAdmin):
    search_fields = ["id"]
    list_display = ["id", "local_run_time", "average_duration"]

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        self._django_jobstore = DjangoJobStore()
        self._memory_jobstore = DjangoMemoryJobStore()

        self._job_queue = []
        self._job_execution_timeout = getattr(
            settings, "APSCHEDULER_RUN_NOW_TIMEOUT", 15
        )
        self._scheduler = BackgroundScheduler({
            'apscheduler.executors.default': {
                'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
                'max_workers': '1'
            }
        })
        self._scheduler.add_jobstore(self._memory_jobstore)
        self._scheduler.add_listener(self._handle_execution_event, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_ERROR | events.EVENT_JOB_MISSED | events.EVENT_JOB_MAX_INSTANCES)
        self._scheduler.start()

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        self.avg_duration_qs = (
            DjangoJobExecution.objects.filter(
                job_id__in=qs.values_list("id", flat=True)
            )
            .order_by("job_id")
            .values_list("job")
            .annotate(avg_duration=Avg("duration"))
        )

        return qs

    def local_run_time(self, obj):
        if obj.next_run_time:
            return util.get_local_dt_format(obj.next_run_time)
        return "(paused)"

    def average_duration(self, obj):
        try:
            return self.avg_duration_qs.get(job_id=obj.id)[1]
        except DjangoJobExecution.DoesNotExist:
            return "None"

    average_duration.short_description = "Average Duration (sec)"

    actions = ["run_selected_jobs"]

    def run_selected_jobs(self, request, queryset):
        start_time = timezone.now()
        for item in queryset:
            django_job = self._django_jobstore.lookup_job(item.id)

            if not django_job:
                msg_dict = {"job_id": item.id}
                msg = _(
                    "Could not find job {job_id} in the database! Skipping execution..."
                )
                self.message_user(
                    request, format_html(msg, **msg_dict), messages.WARNING
                )
                continue

            if self._is_job_running(item.id):
                msg_dict = {"job_id": item.id}
                msg = _(
                    "The job {job_id} is running now! Skipping execution..."
                )
                self.message_user(
                    request, format_html(msg, **msg_dict), messages.WARNING
                )
                continue

            self._scheduler.add_job(
                django_job.func_ref,
                trigger=None,  # Run immediately
                args=django_job.args,
                kwargs=django_job.kwargs,
                id=django_job.id,
                name=django_job.name,
                # misfire_grace_time=django_job.misfire_grace_time,
                misfire_grace_time=600,
                # coalesce=django_job.coalesce,
                coalesce=True,
                max_instances=django_job.max_instances,
            )

            self._job_queue.append(django_job.id)

            msg_dict = {"job_id": django_job.id}
            msg = _("Added the job {job_id} to run now!")
            self.message_user(request, format_html(msg, **msg_dict))

        return None

    def _handle_execution_event(self, event: events.JobExecutionEvent):
        del self._job_queue[self._job_queue.index(event.job_id)]
        if len(self._job_queue) == 0:
            self._scheduler.remove_all_jobs()

    def _is_job_running(self, job_id):
        return job_id in self._job_queue

    run_selected_jobs.short_description = "Run the selected django jobs"


@admin.register(DjangoJobExecution)
class DjangoJobExecutionAdmin(admin.ModelAdmin):
    status_color_mapping = {
        DjangoJobExecution.SUCCESS: "green",
        DjangoJobExecution.SENT: "blue",
        DjangoJobExecution.MAX_INSTANCES: "orange",
        DjangoJobExecution.MISSED: "orange",
        DjangoJobExecution.ERROR: "red",
    }

    list_display = ["id", "job", "html_status", "local_run_time", "duration_text"]
    list_filter = ["job__id", "run_time", "status"]

    def html_status(self, obj):
        return mark_safe(
            f'<p style="color: {self.status_color_mapping[obj.status]}">{obj.status}</p>'
        )

    def local_run_time(self, obj):
        return util.get_local_dt_format(obj.run_time)

    def duration_text(self, obj):
        return obj.duration or "N/A"

    html_status.short_description = "Status"
    duration_text.short_description = "Duration (sec)"
