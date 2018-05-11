import json
import datetime
import logging
import traceback

from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, BooleanField

from web3 import Web3, HTTPProvider

from .models import Student, Professor, University

from .eth_settings import (
                            eth_host,
                            eth_port,
                            default_pass,
                            default_gas,
                            initial_ether_transfer,
                            coinbase_address,
                            coinbase_pass,
                            POA,
                        )

from .settings import SC_ABI, SC_BYTECODE

logger = logging.getLogger(__name__)

#########
# VIEWS #
#########

def root_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    else:
        if request.method == 'POST':
            username = request.POST.get('username', None)
            password = request.POST.get('password', None)
            if username and password:
                user = authenticate(username=username, password=password)
                if user is not None:
                    logger.info(user)
                    login(request, user)
                    return HttpResponseRedirect(reverse('home'))
                else:
                    messages.error(request, "Wrong username or password")
                    return HttpResponseRedirect(reverse('home'))
        return render(request, 'index.html')

def register_user_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    else:
        if request.method == 'POST':
            username = request.POST.get('username', None)
            password = request.POST.get('password', None)
            password2 = request.POST.get('password2', None)
            first_name = request.POST.get('firstname', None)
            last_name = request.POST.get('lastname', None)
            role = request.POST.get('role', None)

            try:
                User.objects.get(username=username)
                messages.error(request, "This user already exists")
                return HttpResponseRedirect(reverse('register_user'))
            except:
                pass

            if password == password2:
                logger.info(f'Creating user {username} with role {role}')
                user = User.objects.create_user(username=username,
                                                password=password,
                                                first_name=first_name,
                                                last_name=last_name
                                                )
                user.save()

                if role == "student":
                    sc_tx = deploy_sc()
                    student = Student()
                    student.user = user
                    student.sc_tx = sc_tx
                    student.save()
                elif role == "professor":
                    eth_address = create_eth_account()
                    professor = Professor()
                    professor.user = user
                    professor.eth_address = eth_address
                    professor.save()
                elif role == "university":
                    eth_address = create_eth_account()
                    university = University()
                    university.user = user
                    university.eth_address = eth_address
                    university.save()
                messages.success(request, "Usuario creado con éxito")
                return HttpResponseRedirect(reverse('root'))
            messages.error(request, "Las contraseñas no coinciden")
            return HttpResponseRedirect(reverse('register_user'))
        else:
            return render(request, 'register_user.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('root'))

@login_required
def home_view(request):
    if hasattr(request.user, 'student'):
        return render(request, 'student.html', get_student_info(request.user.student))
    elif hasattr(request.user, 'professor'):
        return render(request, 'professor.html', {'students': request.user.professor.students.all()})
    elif hasattr(request.user, 'university'):
        return render(request, 'university.html', {'students': Student.objects.all()})

@login_required
def get_professors_view(request, student_name):
    try:
        student = Student.objects.get(user__username=student_name)
    except Student.DoesNotExist:
        return JsonResponse({})
    professors_selected = Professor.objects.filter(students__in=[student]).distinct().order_by('user__first_name')
    professors_not_selected = Professor.objects.exclude(students__in=[student]).distinct().order_by('user__first_name')
    list_professors_selected = professors_to_list(professors_selected, True)
    list_professors_not_selected = professors_to_list(professors_not_selected, False)
    return JsonResponse({'professors': list_professors_selected + list_professors_not_selected})
    
@login_required
def add_professors_view(request):
    if request.method == "POST" and hasattr(request.user, 'university'):
        student_username = request.POST.get('student_username', None)
        new_professors_names = request.POST.getlist('professor', None)

        logger.info(f'Student-> {student_username}')
        logger.info(f'new_professors-> {new_professors_names}')

        if new_professors_names:
            try:
                student = Student.objects.get(user__username=student_username)
            except Student.DoesNotExist:
                logger.error(f'The student {student_username} does not exist')
                return HttpResponseRedirect(reverse('home'))

            new_professors = Professor.objects.filter(user__username__in=new_professors_names)
            for p in new_professors:
                result = add_professor_blockchain(p, student)
                if result:
                    p.students.add(student)
                    p.save()
                else:
                    messages.error(request, f"Error al añadir al profesor {p} en la blockchain")
            messages.success(request, "Añadidos los profesores seleccionados")
        else:
            messages.warning(request, "No se seleccionó ningún profesor")


    return HttpResponseRedirect(reverse('home'))

@login_required
def get_student_info_view(request, student_name):
    try:
        student = Student.objects.get(user__username=student_name)
    except Student.DoesNotExist:
        return JsonResponse({})
    return JsonResponse(get_student_info(student))

@login_required
def add_grade_view(request):
    if request.method == "POST" and hasattr(request.user, 'professor'):

        student_username = request.POST.get('student_username', None)
        subject_number = request.POST.get('subject_number', None)
        grade_value = request.POST.get('grade_value', None)
        
        try:
            student = Student.objects.get(user__username=student_username)
        except Student.DoesNotExist:
            return HttpResponseRedirect(reverse('home'))

        result = add_grade_blockchain(request.user.professor, student, subject_number, grade_value)
        if result:
            messages.success(request, "Asignatura calificada con éxito")
        else:
            messages.error(request, "Error al calificar asignatura")

    
    return HttpResponseRedirect(reverse('home'))

@login_required
def send_thesis_view(request):
    if request.method == "POST" and hasattr(request.user, 'student'):
        thesis_hash = request.POST.get('thesis_hash', None)
        logger.info(f'Sending thesis with hash={thesis_hash}')
        result = send_thesis_blockchain(request.user.student, thesis_hash)
        if result:
            messages.success(request, "Tesis enviada con éxito. Puede tardar unos segundos en validarse en la Blockchain")
        else:
            messages.error(request, "Error al enviar tesis")
    return HttpResponseRedirect(reverse('home'))


#############
# FUNCTIONS #
#############

global_web3 = None

def get_web3():
    global global_web3
    if not global_web3:
        global_web3 = Web3(HTTPProvider('%s:%d' %(eth_host, eth_port)))
        if POA:
            from web3.middleware import geth_poa_middleware
            global_web3.middleware_stack.inject(geth_poa_middleware, layer=0)
    return global_web3

def create_eth_account():
    logger.info('Creating ethereum account')
    try:
        web3 = get_web3()
        eth_address = web3.personal.newAccount(default_pass)
        if initial_ether_transfer > 0:
            web3.personal.unlockAccount(coinbase_address, coinbase_pass)
            web3.eth.sendTransaction(transaction = {
                                                    "from": coinbase_address,
                                                    "to": eth_address,
                                                    "value": web3.toWei(initial_ether_transfer, "ether")
                                                    }
                                                )
        return eth_address
    except:
        logger.error('Error creating new account')
        logger.error(traceback.format_exc())
        return None

def deploy_sc():
    logger.info('Deploying Smart Contract')
    try:
        web3 = get_web3()
        contract = web3.eth.contract(abi=json.loads(SC_ABI), bytecode=SC_BYTECODE)
        university = University.objects.first()
        if not university:
            logger.error('No university available to deploy Smart Contract')
            return None
        logger.info(f'Deploying from {university} with etherum_address={university.eth_address}')
        web3.personal.unlockAccount(university.eth_address, default_pass)
        tx_hash = contract.constructor().transact(transaction={'from': university.eth_address, 'gas': default_gas})
        logger.info(f'tx_hash-> {tx_hash}')
        return tx_hash.hex()
    except:
        logger.error('Error deploying Smart Contract')
        logger.error(traceback.format_exc())
        return None

def get_sc_address(student):
    if not student.sc_address:
        tx_receipt = get_web3().eth.getTransactionReceipt(student.sc_tx)
        if tx_receipt:
            logger.info(f'Updating sc_address for {student.user}')
            student.sc_address = tx_receipt['contractAddress']
            student.save()
    return student.sc_address

def get_student_info(student):
    logger.info(f'Getting student {student} info')
    sc_address = get_sc_address(student)
    if not sc_address:
        return None
    contract = get_web3().eth.contract(address=sc_address, abi=json.loads(SC_ABI))
    grades = []
    for i in range(3):
        grade = contract.functions.grades(i).call()
        grades.append(grade)
    subjects_completed = contract.functions.subjectsCompleted().call()
    degree_obtained = contract.functions.degreeObtained().call()
    return {
            'sc_address': sc_address,
            'grades': grades,
            'subjects_completed': subjects_completed,
            'degree_obtained': degree_obtained,
        }

def add_professor_blockchain(professor, student):
    logger.info(f'Adding proffesor {professor} to student {student}')
    sc_address = get_sc_address(student)
    if not sc_address:
        return False
    web3 = get_web3()

    university = University.objects.first()
    if not university:
        logger.error('No university available to add professor to the Smart Contract')
        return None

    web3.personal.unlockAccount(university.eth_address, default_pass)
    contract = web3.eth.contract(address=sc_address, abi=json.loads(SC_ABI))
    return contract.functions.setProfessor(professor.eth_address).transact(transaction={
                                                                                        'from': university.eth_address, 
                                                                                        'gas': default_gas
                                                                                        }
                                                                                    )

def add_grade_blockchain(professor, student, subject, grade):
    logger.info(f'Professor {professor} adding grade {grade} in subject {subject} to student {student}')
    sc_address = get_sc_address(student)
    if not sc_address:
        return False
    web3 = get_web3()
    web3.personal.unlockAccount(professor.eth_address, default_pass)
    contract = web3.eth.contract(address=sc_address, abi=json.loads(SC_ABI))
    return contract.functions.setGrade(int(subject), int(grade)).transact(transaction={
                                                                            'from': professor.eth_address, 
                                                                            'gas': default_gas
                                                                            }
                                                                        )

def send_thesis_blockchain(student, thesis_hash):
    logger.info(f'Student {student} sending thesis hash to the blockchain')
    sc_address = get_sc_address(student)
    if not sc_address:
        return False

    web3 = get_web3()

    university = University.objects.first()
    if not university:
        logger.error('No university available to add thesis to the Smart Contract')
        return None

    web3.personal.unlockAccount(university.eth_address, default_pass)
    contract = web3.eth.contract(address=sc_address, abi=json.loads(SC_ABI))
    thesis_hash_bytes = bytes.fromhex(thesis_hash)
    return contract.functions.registerThesis(thesis_hash_bytes).transact(transaction={
                                                                                        'from': university.eth_address, 
                                                                                        'gas': default_gas
                                                                                        }
                                                                                    )

def professors_to_list(qs, selected):
    return list(qs.annotate(already_selected=Value(selected, output_field=BooleanField())) \
            .values('user__username', 'user__first_name', 'user__last_name', 'already_selected'))
