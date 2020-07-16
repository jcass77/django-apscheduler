import datetime

from django.contrib import admin
from django.db.models import Avg
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django_apscheduler import util


@admin.register(DjangoJob)
class DjangoJobAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["id", "name", "next_run_time", "average_duration"]

    def get_queryset(self, request):
        self._durations = {
            job: duration
            for job, duration in DjangoJobExecution.objects.filter(
                status=DjangoJobExecution.SUCCESS,
                run_time__gte=now() - datetime.timedelta(days=2),
            )
            .values_list("job")
            .annotate(duration=Avg("duration"))
        }
        return super().get_queryset(request)

    def next_run_time(self, obj):
        if obj.next_run_time is None:
            return "(paused)"
        return util.localize(obj.next_run_time)

    def average_duration(self, obj):
        return self._durations.get(obj.id, "None")

    average_duration.short_description = "Average Duration (sec)"


@admin.register(DjangoJobExecution)
class DjangoJobExecutionAdmin(admin.ModelAdmin):
    status_color_mapping = {
        DjangoJobExecution.ADDED: "RoyalBlue",
        DjangoJobExecution.SENT: "SkyBlue",
        DjangoJobExecution.MAX_INSTANCES: "yellow",
        DjangoJobExecution.MISSED: "yellow",
        DjangoJobExecution.MODIFIED: "yellow",
        DjangoJobExecution.REMOVED: "red",
        DjangoJobExecution.ERROR: "red",
        DjangoJobExecution.SUCCESS: "green",
    }

    list_display = ["id", "job", "html_status", "local_run_time", "duration_text"]
    list_filter = ["job__name", "run_time", "status"]

    def html_status(self, obj):
        return mark_safe(
            f'<p style="color: {self.status_color_mapping[obj.status]}">{obj.status}</p>'
        )

    def local_run_time(self, obj):
        return util.localize(obj.run_time)

    def duration_text(self, obj):
        return obj.duration or "N/A"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("job")

    html_status.short_description = "Status"
