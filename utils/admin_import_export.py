from import_export.admin import ImportExportMixin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm


class ImportExportBase(ImportExportMixin, ModelAdmin):
    """Base admin class for models with import-export functionality."""

    import_form_class = ImportForm
    export_form_class = ExportForm
