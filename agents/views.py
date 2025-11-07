from django.shortcuts import render, redirect
from django.contrib import messages
from agents.models import Agent
from tickets.models import Ticket
from django.contrib.auth import logout
from django.utils import timezone
from django.core.mail import send_mail




def agenthome(request):
    return render(request,'agenthome.html')
def login(request):
    return render(request,'login.html')
# def agent_dashboard(request):
#     agent_id=request.session.get('agent_id')
#     if not agent_id:
#         return redirect('login')
#     agent=Agent.objects.get(id=agent_id)
#     tickets=Ticket.objects.filter(assigned_agent=agent)
#     return render(request,'agent_dashboard.html',{'tickets':tickets,'agent':agent})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from .models import Agent
from tickets.models import Ticket  # Import your Ticket model

def agent_dashboard(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            agent = Agent.objects.get(email=username, password=password)

            # Mark agent as available
            agent.is_available = True
            agent.save()

            # Assign a ticket only if agent has no open tickets
            active_ticket = Ticket.objects.filter(assigned_agent=agent, status='Open').first()
            if not active_ticket:
                unassigned_ticket = Ticket.objects.filter(
                    assigned_agent__isnull=True,
                    status='Open'
                ).order_by('created_at').first()

                if unassigned_ticket:
                    unassigned_ticket.assigned_agent = agent
                    unassigned_ticket.save()
                    agent.last_assigned = timezone.now()
                    agent.is_available = False
                    agent.save()

                    # Notify ticket creator by email
                    send_mail(
                        subject=f"Ticket '{unassigned_ticket.title}' Assigned",
                        message=f"Your ticket '{unassigned_ticket.title}' has been assigned to agent {agent.name}.",
                        from_email=None,
                        recipient_list=[unassigned_ticket.email],
                        fail_silently=False,
                    )

            request.session['agent_id'] = agent.id
            tickets = Ticket.objects.filter(assigned_agent=agent)
            return render(request, 'agent_dashboard.html', {'tickets': tickets, 'agent': agent})

        except Agent.DoesNotExist:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    else:
        # For already logged-in agent
        agent_id = request.session.get('agent_id')
        if agent_id:
            agent = Agent.objects.get(id=agent_id)

            # Ensure no multiple assignments
            active_ticket = Ticket.objects.filter(assigned_agent=agent, status='Open').first()
            if not active_ticket:
                unassigned_ticket = Ticket.objects.filter(
                    assigned_agent__isnull=True,
                    status='Open'
                ).order_by('created_at').first()

                if unassigned_ticket:
                    unassigned_ticket.assigned_agent = agent
                    unassigned_ticket.save()
                    agent.last_assigned = timezone.now()
                    agent.is_available = False
                    agent.save()

                    send_mail(
                        subject=f"Ticket '{unassigned_ticket.title}' Assigned",
                        message=f"Your ticket '{unassigned_ticket.title}' has been assigned to agent {agent.name}.",
                        from_email=None,
                        recipient_list=[unassigned_ticket.email],
                        fail_silently=False,
                    )

            tickets = Ticket.objects.filter(assigned_agent=agent)
            return render(request, 'agent_dashboard.html', {'tickets': tickets, 'agent': agent})
        else:
            return redirect('login')



        
def update_ticket(request, tid):
    agent_id = request.session.get('agent_id')
    if not agent_id:
        return redirect('login')

    agent = Agent.objects.get(id=agent_id)
    ticket = Ticket.objects.get(id=tid, assigned_agent=agent)

    if request.method == 'POST':
        # Close the ticket
        ticket.status = 'Closed'
        ticket.save()

        # Make agent available again
        agent.is_available = True
        agent.save()

        # Notify user that their ticket is resolved
        send_mail(
            subject=f"Ticket '{ticket.title}' Resolved",
            message=f"Your ticket '{ticket.title}' has been resolved by {agent.name}. Thank you for your patience!",
            from_email=None,
            recipient_list=[ticket.email],
            fail_silently=False,
        )

        # Assign next ticket automatically if any available
        next_ticket = Ticket.objects.filter(assigned_agent__isnull=True, status='Open').order_by('created_at').first()
        if next_ticket:
            next_ticket.assigned_agent = agent
            next_ticket.save()
            agent.is_available = False
            agent.last_assigned = timezone.now()
            agent.save()

            send_mail(
                subject=f"Ticket '{next_ticket.title}' Assigned",
                message=f"Your ticket '{next_ticket.title}' has been assigned to agent {agent.name}.",
                from_email=None,
                recipient_list=[next_ticket.email],
                fail_silently=False,
            )

        messages.success(request, f'Ticket "{ticket.title}" marked as closed.')
        return redirect('agent_dashboard')

    return render(request, 'update_ticket.html', {'ticket': ticket})


def logout_agent(request):
    agent_id = request.session.get('agent_id')
    if agent_id:
        agent = Agent.objects.get(id=agent_id)
        agent.is_available = False
        agent.save()
        # del request.session['agent_id']
        logout(request)

    return redirect('login')