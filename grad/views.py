from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.http import HttpResponseRedirect
from grad.models import GradStudent, GradProgram, Supervisor, GradRequirement, CompletedRequirement, GradStatus, \
        ScholarshipType, Scholarship, Promise, OtherFunding, LetterTemplate,\
    Letter
from grad.forms import SupervisorForm, PotentialSupervisorForm, GradAcademicForm, GradProgramForm, \
        GradStudentForm, GradStatusForm, GradRequirementForm, possible_supervisors, BaseSupervisorsFormSet,\
    SearchForm, LetterTemplateForm, LetterForm
from coredata.models import Person, Role, Unit, Semester, CAMPUS_CHOICES
#from django.template import RequestContext
from django import forms
from django.forms.models import modelformset_factory, inlineformset_factory
from courselib.auth import requires_role
import datetime
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib import messages
from log.models import LogEntry
from django.db.models import Q
from django.utils.encoding import iri_to_uri

# get semester based on input datetime. defaults to today
# returns semseter object
def get_semester(date=datetime.date.today()):
    year = date.year
    next_sem = 0
    for s in Semester.objects.filter(start__year=year).order_by('-start'):
        if next_sem == 1:
            # take this semster
            return s
        if date > s.start:
            if date < s.end :
                return s
            else:
                #take the next semseter
                next_sem = 1

@requires_role("GRAD")
def index(request):
    grads = GradStudent.objects.all()
    paginator = Paginator(grads, 5)
    
    try: 
        p = int(request.GET.get("page", '1'))
    except ValueError: p = 1

    try:
        grads_page = paginator.page(p)
    except (InvalidPage, EmptyPage):
        grads_page = paginator.page(paginator.num_pages)    
    
    # set frontend defaults
    page_title = 'Graduate Student Records'  
    crumb = 'Grads' 
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'grads': grads,
               'grads_page': grads_page               
               }
    return render(request, 'grad/index.html', context)


@requires_role("GRAD")
def view_all(request, grad_slug):
    # will display academic, personal, FIN, status history, supervisor
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    supervisors = Supervisor.objects.filter(student=grad)
    status_history = get_list_or_404(GradStatus, student=grad, hidden=False)
    
    #calculate missing reqs
    completed_req = CompletedRequirement.objects.filter(student=grad)
    req = GradRequirement.objects.filter(program=grad.program)
    missing_req = req    
    for s in completed_req:
        missing_req = missing_req.exclude(description=s.requirement.description)
    
    # set frontend defaults
    page_title = "%s 's Graduate Student Record" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)

    gp = grad.person.get_fields
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'grad' : grad,
               'gp' : gp,
               'status_history' : status_history,
               'supervisors' : supervisors,
               'completed_req' : completed_req,
               'missing_req' : missing_req         
               }
    return render(request, 'grad/view_all.html', context)


@requires_role("GRAD")
def manage_supervisors(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    supervisors = Supervisor.objects.filter(student=grad, position__gte=1).select_related('supervisor')
    supervisor_people = [s.supervisor for s in supervisors if s.supervisor]
    # Using filter because get returns an error when there are no matching queries
    pot_supervisor = Supervisor.objects.filter(student=grad, position=0) 
    # Initialize potential supervisor to first on of the list of results
    # There should be exactly one match unless there is data error
    extra_form = 0
    if(supervisors.count() == 0):
        extra_form = 1
    if (pot_supervisor.count() == 0):
        pot_supervisor = None
    else:
        pot_supervisor = pot_supervisor[0]
        
    supervisors_formset = modelformset_factory(Supervisor, form=SupervisorForm, extra=extra_form, max_num=4)(queryset=supervisors,prefix="form")
    for f in supervisors_formset:
        f.set_supervisor_choices(possible_supervisors([grad.program.unit], extras=supervisor_people))
        f.fields['position'].widget = forms.HiddenInput()
        if(extra_form == 1):
            f.fields['position'].initial = 1

    if request.method == 'POST':
        potential_supervisors_form = PotentialSupervisorForm(request.POST, instance=pot_supervisor, prefix="pot_sup")
        if potential_supervisors_form.is_valid():
            #change gradstudent's last updated/by info to newest
            grad.updated_at = datetime.datetime.now()
            grad.created_by = request.user.username  
            grad.save()                
            superF = potential_supervisors_form.save(commit=False)
            superF.modified_by = request.user.username
            superF.student = grad #Passing grad student info to model
            superF.position = 0   #Hard coding potential supervisor and passing to model
            superF.save()
            messages.success(request, "Updated Potential Supervisor for %s." % (potential_supervisors_form.instance.student))
            l = LogEntry(userid=request.user.username,
                  description="Updated Potential Supervisor for %s." % (potential_supervisors_form.instance.student),
                  related_object=potential_supervisors_form.instance)
            l.save()              
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':grad_slug}))
    else:
        potential_supervisors_form = PotentialSupervisorForm(instance=pot_supervisor, prefix="pot_sup")
        potential_supervisors_form.set_supervisor_choices(possible_supervisors([grad.program.unit]))

    # set frontend defaults
    page_title = "%s's Supervisor(s) Record" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)
    gp = grad.person.get_fields 
    context = {
               'supervisors_formset': supervisors_formset,
               'potential_supervisors_form': potential_supervisors_form,
               'page_title' : page_title,
               'crumb' : crumb,
               'grad' : grad,
               'gp' : gp,
               }
    return render(request, 'grad/manage_supervisors.html', context)

@requires_role("GRAD")
def update_supervisors(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    supervisors = Supervisor.objects.filter(student=grad, position__gte=1).select_related('supervisor')
    supervisor_people = [s.supervisor for s in supervisors if s.supervisor]
    if request.method == 'POST':
        supervisors_formset = modelformset_factory(Supervisor, form=SupervisorForm, formset=BaseSupervisorsFormSet)(request.POST,prefix="form")
        for f in supervisors_formset:
            f.set_supervisor_choices(possible_supervisors([grad.program.unit], extras=supervisor_people))
            f.fields['position'].widget = forms.HiddenInput()
        
        if supervisors_formset.is_valid():
            #change gradstudent's last updated info to newest
            grad.updated_at = datetime.datetime.now()
            grad.created_by = request.user.username  
            grad.save()
            for s in supervisors_formset:
                if (not s.cleaned_data['supervisor'] == None or s.cleaned_data['external'] == None):
                    s.instance.student = grad
                else:
                    s.cleaned_data = None
                    s._changed_data = []
                    
            supervisors_formset.save()
            messages.success(request, "Updated Supervisor(s) for %s." % (grad))
            l = LogEntry(userid=request.user.username,
                  description="Updated Supervisor(s) for %s." % (grad),
                  related_object=grad)
            l.save()
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':grad_slug}))
        else:
            page_title = "%s's Supervisor(s) Record" % (grad.person.first_name)
            crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)
            gp = grad.person.get_fields 
            context = {
               'supervisors_formset': supervisors_formset,
               #'potential_supervisors_form': potential_supervisors_form,
               'page_title' : page_title,
               'crumb' : crumb,
               'grad' : grad,
               'gp' : gp,
               }
            return render(request, 'grad/manage_supervisors.html', context)
            #return HttpResponseRedirect(reverse(manage_supervisors, kwargs={'grad_slug':grad_slug}))

    else:
        return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug': grad_slug}))

@requires_role("GRAD")
def manage_requirements(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)    
    
    #calculate/find missing reqs
    completed_req = CompletedRequirement.objects.filter(student=grad)
    req = GradRequirement.objects.filter(program=grad.program)
    req_choices = [(u'', u'\u2014')] + [(r.id, r.description) for r in req]
    missing_req = req    
    for s in completed_req:
        missing_req = missing_req.exclude(description=s.requirement.description)
    num_missing = req.count()
    
    ReqFormSet = inlineformset_factory(GradStudent, CompletedRequirement, max_num=num_missing, can_order=False) 
    if request.method == 'POST':
        req_formset = ReqFormSet(request.POST, request.FILES, instance=grad, prefix='req')
        for f in req_formset:
            f.fields['requirement'].choices = req_choices 

        if req_formset.is_valid():
            #change gradstudent's last updated info to newest
            grad.updated_at = datetime.datetime.now()
            grad.created_by = request.user.username            
            grad.save()
            req_formset.save()
            messages.success(request, "Updated Grad Requirements for %s." % (req_formset.instance.person))
            l = LogEntry(userid=request.user.username,
                  description="Updated Grad Requirements for %s." % (req_formset.instance.person),
                  related_object=req_formset.instance)
            l.save()   
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':grad_slug}))
    else:
        req_formset = ReqFormSet(instance=grad, prefix='req')
        for f in req_formset:
            f.fields['requirement'].choices = req_choices

    # set frontend defaults
    page_title = "%s's Requirements Record" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)
    gp = grad.person.get_fields     
    context = {
               'req_formset': req_formset,
               'page_title' : page_title,
               'crumb' : crumb,
               'gp' : gp,
               'grad' : grad,
               'missing_req' : missing_req     
               }
    return render(request, 'grad/manage_requirements.html', context)


@requires_role("GRAD")
def manage_academics(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    
    if request.method == 'POST':
        grad_form = GradAcademicForm(request.POST, instance=grad, prefix="grad")
        if grad_form.is_valid():
            gradF = grad_form.save(commit=False)
            gradF.modified_by = request.user.username
            grad.slug = None
            gradF.save()
            messages.success(request, "Updated Grad Academics for %s." % (grad_form.instance.person))
            l = LogEntry(userid=request.user.username,
                  description="Updated Grad Academics for %s." % (grad_form.instance.person),
                  related_object=grad_form.instance)
            l.save()    
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':grad.slug}))
    else:
        grad_form = GradAcademicForm(instance=grad, prefix="grad")

    # set frontend defaults
    page_title = "%s 's Graduate Academic Record" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)
    gp = grad.person.get_fields 
    context = {
               'grad_form': grad_form,
               'page_title' : page_title,
               'crumb' : crumb,
               'grad' : grad,
               'gp' : gp,
               }
    return render(request, 'grad/manage_academics.html', context)


@requires_role("GRAD")
def manage_status(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    status_history = get_list_or_404(GradStatus, student=grad.id, hidden=False)

    if request.method == 'POST':
        new_status_form = GradStatusForm(request.POST)
        if new_status_form.is_valid():
            # Close previous status
            # Assuming that only one status can be unclosed at once.
            old_status_end = new_status_form.instance.start.previous_semester()
            old_status_start = GradStatus.objects.get(student=grad, end=None).start

            # Status should not be negative in length, but end in the semester they started.
            if old_status_start > old_status_end:
                old_status_end = old_status_start

            GradStatus.objects.filter(student=grad, end=None).update(end=old_status_end)

            # Save new status
            new_actual_status = new_status_form.save(commit=False)
            new_actual_status.student = grad
            new_actual_status.save()
            
            #change gradstudent's last updated/by info to newest
            grad.updated_at = datetime.datetime.now()
            grad.created_by = request.user.username
            grad.save()
            
            messages.success(request, "Updated Status History for %s." % (grad.person))
            l = LogEntry(userid=request.user.username,
                    description="Updated Status History for %s." % (grad.person),
                    related_object=new_status_form.instance)
            l.save()                       
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':grad_slug}))
    else:
        new_status_form = GradStatusForm()

    # set frontend defaults
    page_title = "%s 's Status Record" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.first_name, grad.person.last_name)
    gp = grad.person.get_fields
    context = {
               'new_status' : new_status_form,
               'status_history' : status_history,
               'page_title' : page_title,
               'crumb' : crumb,
               'grad' : grad,
               'gp' : gp
               }
    return render(request, 'grad/manage_status.html', context)
    
@requires_role("GRAD")
def new(request):
    if request.method == 'POST':
        grad_form = GradStudentForm(request.POST, prefix="grad")
        supervisors_form = PotentialSupervisorForm(request.POST, prefix="sup")
        status_form = GradStatusForm(request.POST, prefix="stat")
        if grad_form.is_valid() and supervisors_form.is_valid() and status_form.is_valid() :
            gradF = grad_form.save(commit=False)
            gradF.created_by = request.user.username
            gradF.save()
            superF = supervisors_form.save(commit=False)
            supervisors_form.cleaned_data["student"] = gradF
            superF.student_id = gradF.id
            superF.position = 0
            superF.created_by = request.user.username
            supervisors_form.save()
            statusF = status_form.save(commit=False)
            status_form.cleaned_data["student"] = gradF
            statusF.created_by = request.user.username
            statusF.student_id = gradF.id
            status_form.save()
            messages.success(request, "Created new grad student %s." % (grad_form.instance.person))
            l = LogEntry(userid=request.user.username,
                  description="Created new grad student %s." % (grad_form.instance.person),
                  related_object=grad_form.instance)
            l.save()           
            return HttpResponseRedirect(reverse(view_all, kwargs={'grad_slug':gradF.slug}))
    else:
        prog_list = get_list_or_404(GradProgram)
        grad_form = GradStudentForm(prefix="grad", initial={'program': prog_list[0], 'campus': CAMPUS_CHOICES[0][0] })
        supervisors_form = PotentialSupervisorForm(prefix="sup",)  
        status_form = GradStatusForm(prefix="stat", initial={'status': 'ACTI', 'start': get_semester() })  
        #initial: 'start' returns nothing if there are no future semester available in DB 

    # set frontend defaults
    page_title = 'New Graduate Student Record'
    crumb = 'New Grad' 
    context = {
               'grad_form': grad_form,
               #'req_form': req_form,
               'supervisors_form': supervisors_form,
               'status_form': status_form,
               'page_title' : page_title,
               'crumb' : crumb
               }
    return render(request, 'grad/new.html', context)

@requires_role("GRAD")
def new_program(request):
    unit_choices = [(u.id, u.name) for u in request.units]
    if request.method == 'POST':
        form = GradProgramForm(request.POST)
        form.fields['unit'].choices = unit_choices 
        if form.is_valid():
            form.save()
            messages.success(request, "Created new program %s for %s." % (form.instance.label, form.instance.unit))
            l = LogEntry(userid=request.user.username,
                  description="Created new program %s for %s." % (form.instance.label, form.instance.unit),
                  related_object=form.instance)
            l.save()                        
            return HttpResponseRedirect(reverse(programs))
    else:
        form = GradProgramForm()    
        form.fields['unit'].choices = unit_choices

    page_title = 'New Program'  
    crumb = 'New Program' 
    context = {
               'form': form,
               'page_title' : page_title,
               'crumb' : crumb
               }
    return render(request, 'grad/new_program.html', context)

@requires_role("GRAD")
def programs(request):
    programs = GradProgram.objects.filter(unit__in=request.units)
    
    # set frontend defaults
    page_title = 'Graduate Programs Records'
    crumb = 'Grad Programs' 
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'programs': programs               
               }
    return render(request, 'grad/programs.html', context)

@requires_role("GRAD")
def requirements(request):
    requirements = GradRequirement.objects.filter(program__unit__in=request.units)

    page_title = 'Graduate Requirements'
    crumb = 'Grad Requirements'     
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'requirements': requirements                 
               }
    return render(request, 'grad/requirements.html', context)

@requires_role("GRAD")
def new_requirement(request):
    program_choices = [(p.id, p.label) for p in GradProgram.objects.filter(unit__in=request.units)]
    if request.method == 'POST':
        form = GradRequirementForm(request.POST)
        form.fields['program'].choices = program_choices
        if form.is_valid():
            form.save()
            messages.success(request, "Created new grad requirement %s in %s." % (form.instance.description, form.instance.program))
            l = LogEntry(userid=request.user.username,
                  description="Created new grad requirement %s in %s." % (form.instance.description, form.instance.program),
                  related_object=form.instance)
            l.save()            
            return HttpResponseRedirect(reverse(requirements))
    else:
        form = GradRequirementForm()
        form.fields['program'].choices = program_choices

    page_title = 'New Requirement'  
    crumb = 'New Requirement' 
    context = {
               'form': form,
               'page_title' : page_title,
               'crumb' : crumb
               }
    return render(request, 'grad/new_requirement.html', context)

@requires_role("GRAD")
def letter_templates(request):
    templates = LetterTemplate.objects.filter(unit__in=request.units)

    page_title = 'Letter Templates'
    crumb = 'Letter Templates'     
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'templates': templates                 
               }
    return render(request, 'grad/letter_templates.html', context)

@requires_role("GRAD")
def new_letter_template(request):
    unit_choices = [(u.id, u.name) for u in request.units]
    if request.method == 'POST':
        form = LetterTemplateForm(request.POST)
        form.fields['unit'].choices = unit_choices 
        if form.is_valid():
            f = form.save(commit=False)
            f.created_by = request.user.username            
            f.save()
            messages.success(request, "Created new letter template %s in %s." % (form.instance.label, form.instance.unit))
            l = LogEntry(userid=request.user.username,
                  description="Created new letter template %s in %s." % (form.instance.label, form.instance.unit),
                  related_object=form.instance)
            l.save()            
            return HttpResponseRedirect(reverse(letter_templates))
    else:
        form = LetterTemplateForm()
        form.fields['unit'].choices = unit_choices 

    page_title = 'New Letter Template'  
    crumb = 'New' 
    context = {
               'form': form,
               'page_title' : page_title,
               'crumb' : crumb
               }
    return render(request, 'grad/new_letter_template.html', context)


@requires_role("GRAD")
def letters(request):
    letters = Letter.objects.filter(template__unit__in=request.units)

    page_title = 'Letters'
    crumb = 'Letters'     
    context = {
               'page_title' : page_title,
               'crumb' : crumb,
               'letters': letters                 
               }
    return render(request, 'grad/letters.html', context)

@requires_role("GRAD")
def new_letter(request):

    if request.method == 'POST':
        form = LetterForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.created_by = request.user.username            
            f.save()
            messages.success(request, "Created new %s letter for %s." % (form.instance.template.label, form.instance.student))
            l = LogEntry(userid=request.user.username,
                  description="Created new %s letter for %s." % (form.instance.template.label, form.instance.student),
                  related_object=form.instance)
            l.save()            
            return HttpResponseRedirect(reverse(letters))
    else:
        form = LetterForm()

    page_title = 'New Letter'  
    crumb = 'New' 
    context = {
               'form': form,
               'page_title' : page_title,
               'crumb' : crumb
               }
    return render(request, 'grad/new_letter.html', context)


@requires_role("GRAD")
def search(request):
    if len(request.GET) == 0:
        form = SearchForm()
    else:
        form = SearchForm(request.GET)
    if form.is_valid():
        query_string = iri_to_uri(request.META.get('QUERY_STRING',''))
        #TODO: add a button to save the search
        #TODO: prefill common querys
        #TODO: add a model to save these queries; save the query string
        query = Q()
        #TODO: construct search query from form's data
        #NOTE: use getlist on request.GET rather than __getitem__
        
        grads = GradStudent.objects.filter(query)
        
        context = {
                   'page_title' : 'Graduate Student Search Results',
                   'crumb' : 'Grads',
                   'grads': grads,
                   }
        return render(request, 'grad/search_results.html', context)
    else:
        page_title = 'Graduate Student Advanced Search'
        context = {
                   'page_title' : page_title,
                   'form':form
                   }
        return render(request, 'grad/search.html', context)


@requires_role("GRAD")
def financials(request, grad_slug):
    grad = get_object_or_404(GradStudent, slug=grad_slug)
    status_history = get_list_or_404(GradStatus, student=grad, hidden=False)
    
    scholarship = Scholarship.objects.all()
    type = ScholarshipType.objects.all()
    promise = Promise.objects.all()
    other = OtherFunding.objects.all()
    
   
    
    # set frontend defaults
    page_title = "%s's Financial Summary" % (grad.person.first_name)
    crumb = "%s, %s" % (grad.person.last_name, grad.person.first_name)

    context = {'scholarship':scholarship,
               'type':type,
               'promise':promise,
               'other':other,
               'page_title':page_title,
               'crumb':crumb,
               'grad':grad,
               
               }
    return render(request,'grad/view_financials.html',context)
    
