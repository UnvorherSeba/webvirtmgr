import socket

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.datastructures import SortedDict

from instance.models import Host
from servers.forms import HostAddTcpForm, HostAddSshForm


def index(request):
    """

    Index page.

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')
    else:
        return HttpResponseRedirect('/servers')


def servers_list(request):
    """

    Dashboard page.

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def get_hosts_status(hosts):
        """

        Function return all hosts all vds on host

        """
        all_hosts = {}
        for host in hosts:
            try:
                socket_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_host.settimeout(1)
                if host.type == 'ssh':
                    socket_host.connect((host.hostname, 22))
                if host.type == 'tcp':
                    socket_host.connect((host.hostname, 16509))
                socket_host.close()
                status = 1
            except Exception as err:
                status = err
            all_hosts[host.id] = (host.name, host.hostname, status)
        return all_hosts

    hosts = Host.objects.filter()
    hosts_info = get_hosts_status(hosts)
    form = None

    if request.method == 'POST':
        if 'host_del' in request.POST:
            del_host = Host.objects.get(id=request.POST.get('host_id', ''))
            del_host.delete()
            return HttpResponseRedirect(request.get_full_path())
        if 'host_tcp_add' in request.POST:
            form = HostAddTcpForm(request.POST)
            print form.errors
            if form.is_valid():
                data = form.cleaned_data
                new_tcp_host = Host(name=data['name'],
                                hostname=data['hostname'],
                                type='tcp',
                                login=data['login'],
                                password=data['password']
                                )
                new_tcp_host.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'host_ssh_add' in request.POST:
            form = HostAddSshForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                new_ssh_host = Host(name=data['name'],
                                hostname=data['hostname'],
                                type='ssh',
                                login=data['login']
                                )
                new_ssh_host.save()
                return HttpResponseRedirect(request.get_full_path())

    return render_to_response('dashboard.html', {'hosts_info': hosts_info,
                                                 'form': form,
                                                 },
                              context_instance=RequestContext(request))


def infrastructure(request):
    """

    Infrastructure page.

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    hosts = Host.objects.filter().order_by('id')
    hosts_vms = {}
    host_info = None
    host_mem = None

    for host in hosts:
        try:
            import socket
            socket_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_host.settimeout(1)
            if host.type == 'ssh':
                socket_host.connect((host.hostname, host.port))
            else:
                socket_host.connect((host.hostname, 16509))
            socket_host.close()
            status = 1
        except Exeption:
            status = 2

        if status == 1:
            conn = ConnServer(host)
            host_info = conn.node_get_info()
            host_mem = conn.memory_get_usage()
            hosts_vms[host.id, host.name, status, host_info[2], host_mem[0], host_mem[2]] = conn.vds_on_cluster()
        else:
            hosts_vms[host.id, host.name, status, None, None, None] = None

    for host in hosts_vms:
        hosts_vms[host] = sort_host(hosts_vms[host])

    return render_to_response('infrastructure.html', {'hosts_info': host_info,
                                                      'host_mem': host_mem,
                                                      'hosts_vms': hosts_vms,
                                                      'hosts': hosts
                                                      },
                              context_instance=RequestContext(request))


def page_setup(request):
    return render_to_response('setup.html', {}, context_instance=RequestContext(request))