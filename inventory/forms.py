from .models import Asset, AssetDocumentAttachment, AssetChangeRecord, CATEGORY_CHOICES
from outreach.models import OutreachEvent
from django import forms
from coredata.models import Unit
from coredata.widgets import CalendarWidget, DollarInput
from coredata.forms import PersonField
import datetime

class AssetForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(AssetForm, self).__init__(*args, **kwargs)
        unit_ids = [unit.id for unit in request.units]
        units = Unit.objects.filter(id__in=unit_ids)
        self.fields['unit'].queryset = units
        self.fields['unit'].empty_label = None
        SORTED_CATEGORIES = sorted(CATEGORY_CHOICES, key=lambda x: x[1])
        self.fields['category'].choices = SORTED_CATEGORIES

    class Meta:
        exclude = []
        model = Asset
        widgets = {
            'notes': forms.Textarea,
            'price': DollarInput,
            'last_order_date': CalendarWidget,
            'vendor': forms.Textarea,
        }


class AssetAttachmentForm(forms.ModelForm):
    class Meta:
        model = AssetDocumentAttachment
        exclude = ("asset", "created_by")


class AssetChangeForm(forms.ModelForm):
    person = PersonField()

    def __init__(self, request, *args, **kwargs):
        super(AssetChangeForm, self).__init__(*args, **kwargs)
        #  The following two lines look stupid, but they are not.  request.units contains a set of units.
        #  in order to be used this way, we need an actual queryset.
        #
        #  In this case, we also include subunits.  If you manage assets for a parent unit, chances are you may be
        #  adding/removing them for events in your children units.
        unit_ids = [unit.id for unit in Unit.sub_units(request.units)]
        units = Unit.objects.filter(id__in=unit_ids)

    class Meta:
        model = AssetChangeRecord
        widgets = {
            'date': CalendarWidget
        }
        fields = ['person', 'qty', 'date']

    def is_valid(self, *args, **kwargs):
        PersonField.person_data_prep(self)
        return super(AssetChangeForm, self).is_valid(*args, **kwargs)
