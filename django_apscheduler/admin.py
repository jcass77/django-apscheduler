from django.contrib import admin

from django_apscheduler.models import DjangoJob, DjangoJobExecution


class DjangoJobAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "next_run_time"]

class DjangoJobExecutionAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "html_status", "run_time", "duration"]

    list_filter = ["job__name", "run_time", "status"]

    def get_queryset(self, request):
        return super(DjangoJobExecutionAdmin, self).get_queryset(
            request
        ).select_related("job")

admin.site.register(DjangoJob, DjangoJobAdmin)
admin.site.register(DjangoJobExecution, DjangoJobExecutionAdmin)