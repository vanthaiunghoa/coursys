from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, render
from django.http import HttpResponse
from advisornotes.models import AdvisorNote
from coredata.models import Person, Role
from django.template import RequestContext
from courselib.auth import *
from forms import *

@requires_advisor()
def all_notes(request):
    #advisor should only see notes from his/her department
    #notes = AdvisorNote.objects.all()
    dept = [r.department for r in Role.objects.filter(person__userid=request.user.username)]
    notes = AdvisorNote.objects.filter(department=dept[0])
    return render_to_response("advisornotes/all_notes.html", {'notes': notes}, context_instance=RequestContext(request))

@requires_advisor()
def new_note(request):
    if request.method == 'POST':
        form = AdvisorNoteForm(request.POST)
        if form.is_valid():
            form.save()
            """
            #LOG EVENT#
            l = LogEntry(userid=request.user.username,
                  description=("new note: for %s") % (form.instance.student),
                  related_object=form.instance)
            l.save()
            """
            return HttpResponseRedirect(reverse(all_notes))
    else:
        form = AdvisorNoteForm()
    return render(request, 'advisornotes/new_note.html', {'form': form})
