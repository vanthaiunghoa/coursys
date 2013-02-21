from django.core.urlresolvers import reverse, resolve
from django.core.mail.message import EmailMessage
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response, get_object_or_404, render
from datetime import date
from urlparse import urlparse
from courselib.auth import requires_role, HttpResponseRedirect, \
    ForbiddenResponse, requires_course_staff_by_slug
from grades.models import Activity
from peerreview.forms import AddPeerReviewComponentForm
from peerreview.models import *

@requires_course_staff_by_slug
def add_peer_review_component(request, course_slug, activity_slug):
    activity = get_object_or_404(Activity, slug = activity_slug)
    class_size = activity.offering.members.count()
    if request.method == 'POST':
        form = AddPeerReviewComponentForm(class_size, request.POST)
        if form.is_valid():
            try: #see if peerreview component already exists for this activity
                peerreview_component = PeerReviewComponent.objects.get(pk=activity.pk)
                peerreview_component.due_date = form.cleaned_data['due_date']
                peerreview_component.number_of_reviews = form.cleaned_data['number_of_reviews']
                peerreview_component.save()
            except: #else create a peerreview component
                peerreview_component = PeerReviewComponent.objects.create(
                    activity = activity,
                    due_date = form.cleaned_data['due_date'],
                    number_of_reviews = form.cleaned_data['number_of_reviews'],
                )
            return HttpResponseRedirect(reverse('grades.views.activity_info', kwargs={'course_slug': course_slug, 'activity_slug': activity_slug}))
    else:
        form = AddPeerReviewComponentForm(class_size)

    context = {
        'form' : form,
        'course_slug' : course_slug,
        'activity_slug' : activity_slug,
    }
    return render(request, "peerreview/add_peer_review_component.html", context)

