from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from .models import Asset
from .forms import AssetForm, AssetAttachmentForm
from courselib.auth import requires_role
from log.models import LogEntry
from coredata.models import Unit, Role, Person
from courselib.auth import ForbiddenResponse
from django.db import transaction
from django.http import StreamingHttpResponse


def _has_unit_role(user, asset):
    """
    A quick method to check that the person has the Inventory Admin role for the given asset's unit.
    """
    return Role.objects.filter(person__userid=user.username, role='INV', unit=asset.unit).count() > 0

@requires_role('INV')
def inventory_index(request):
    unit_ids = [unit.id for unit in request.units]
    units = Unit.objects.filter(id__in=unit_ids)
    assets = Asset.objects.visible(units)
    return render(request, 'inventory/index.html', {'assets': assets})


@requires_role('INV')
def new_asset(request):
    if request.method == 'POST':
        form = AssetForm(request, request.POST)
        if form.is_valid():
            asset = form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 u'Asset was created')
            l = LogEntry(userid=request.user.username,
                         description="Added asset %s" % asset.name,
                         related_object=asset)
            l.save()
            return HttpResponseRedirect(reverse('inventory:inventory_index'))
    else:
        form = AssetForm(request)
    return render(request, 'inventory/new_asset.html', {'form': form})


@requires_role('INV')
def edit_asset(request, asset_slug):
    asset = get_object_or_404(Asset, slug=asset_slug)
    if not _has_unit_role(request.user, asset):
        return ForbiddenResponse(request)
    if request.method == 'POST':
        form = AssetForm(request, request.POST, instance=asset)
        if form.is_valid():
            asset = form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 u'Asset was modified')
            l = LogEntry(userid=request.user.username,
                         description="Modified asset %s" % asset.name,
                         related_object=asset)
            l.save()
            return HttpResponseRedirect(reverse('inventory:inventory_index'))
    else:
        form = AssetForm(request, instance=asset)
    return render(request, 'inventory/edit_asset.html', {'form': form, 'asset_slug': asset_slug})


@requires_role('INV')
def view_asset(request, asset_slug):
    asset = get_object_or_404(Asset, slug=asset_slug)
    if not _has_unit_role(request.user, asset):
        return ForbiddenResponse(request)
    return render(request, 'inventory/view_asset.html', {'asset': asset})


@requires_role('INV')
def delete_asset(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    if not _has_unit_role(request.user, asset):
        return ForbiddenResponse(request)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Hid asset %s' % asset)
        l = LogEntry(userid=request.user.username,
                     description="Deleted asset: %s" % asset,
                     related_object=asset)
        l.save()
    return HttpResponseRedirect(reverse('inventory:inventory_index'))


@requires_role('INV')
@transaction.atomic
def new_attachment(request, asset_id):
    asset = get_object_or_404(Asset, pk=asset_id)
    editor = get_object_or_404(Person, userid=request.user.username)

    form = AssetAttachmentForm()
    context = {"asset": asset,
               "attachment_form": form}

    if request.method == "POST":
        form = AssetAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.asset = asset
            attachment.created_by = editor
            upfile = request.FILES['contents']
            filetype = upfile.content_type
            if upfile.charset:
                filetype += "; charset=" + upfile.charset
            attachment.mediatype = filetype
            attachment.save()
            return HttpResponseRedirect(reverse('inventory:view_asset', kwargs={'asset_slug': asset.slug}))
        else:
            context.update({"attachment_form": form})

    return render(request, 'inventory/asset_document_attachment_form.html', context)


@requires_role('INV')
def view_attachment(request, asset_id, attach_slug):
    asset = get_object_or_404(Asset, pk=asset_id)
    attachment = get_object_or_404(asset.attachments.all(), slug=attach_slug)
    filename = attachment.contents.name.rsplit('/')[-1]
    resp = StreamingHttpResponse(attachment.contents.chunks(), content_type=attachment.mediatype)
    resp['Content-Disposition'] = 'inline; filename="' + filename + '"'
    resp['Content-Length'] = attachment.contents.size
    return resp


@requires_role('INV')
def download_attachment(request, asset_id, attach_slug):
    asset = get_object_or_404(Asset, pk=asset_id)
    attachment = get_object_or_404(asset.attachments.all(), slug=attach_slug)
    filename = attachment.contents.name.rsplit('/')[-1]
    resp = StreamingHttpResponse(attachment.contents.chunks(), content_type=attachment.mediatype)
    resp['Content-Disposition'] = 'attachment; filename="' + filename + '"'
    resp['Content-Length'] = attachment.contents.size
    return resp


@requires_role('INV')
def delete_attachment(request, asset_id, attach_slug):
    asset = get_object_or_404(Asset, pk=asset_id)
    attachment = get_object_or_404(asset.attachments.all(), slug=attach_slug)
    attachment.hide()
    messages.add_message(request,
                         messages.SUCCESS,
                         u'Attachment deleted.'
                         )
    l = LogEntry(userid=request.user.username, description="Hid attachment %s" % attachment, related_object=attachment)
    l.save()
    return HttpResponseRedirect(reverse('inventory:view_asset', kwargs={'asset_slug': asset.slug}))