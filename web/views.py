import json
import datetime
import logging
import random
import requests
import traceback

from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .decorators import registrador_only
from .models import ProductType, Registrador


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
                user = authenticate(username=username, password=password)  # Auntenticamos el usuario
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
            email = request.POST.get('email', None)
            registrador = request.POST.get('registrador', None)

            try:
                User.objects.get(username=username)
                messages.error(request, "This user already exists")
                return HttpResponseRedirect(reverse('register_user'))
            except:
                pass

            if password == password2:
                try:
                    data={
                        "$class": "org.example.mynetwork.UserParticipant",
                        "participantId": username,
                        "firstName": first_name,
                        "lastName": last_name,
                        }
                    if registrador:
                        data['rol'] = "Recorder"
                    else:
                        data['rol'] = "Owner"

                    send_post(api="UserParticipant", data=data)
                    user = User.objects.create_user(username=username,
                                                    email=email,
                                                    password=password,
                                                    first_name=first_name,
                                                    last_name=last_name
                                                    )
                    user.save()
                    if registrador:
                        r = Registrador()
                        r.user = user
                        r.save()
                    messages.success(request, "Usuario creado con éxito")
                    return HttpResponseRedirect(reverse('home'))
                except:
                    logger.error(traceback.format_exc())
                    messages.error(request, "Error creating the account")
                    return HttpResponseRedirect(reverse('register_user'))
            else:
                messages.error(request, "Both passwords have to be the same")
                return HttpResponseRedirect(reverse('register_user'))
        else:
            return render(request, 'register_user.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('root'))

@login_required
def home_view(request):
    return HttpResponseRedirect(reverse('products'))

@login_required
def products_view(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id', None)
        new_owner = request.POST.get('new_owner', None)
        logger.info("Transfering product with id=%s from %s to %s" %(product_id, request.user, new_owner))
        if request.user.username == new_owner:
            messages.error(request, "You can't transfer the product to yourself!")
            return HttpResponseRedirect(reverse('products'))

        try:
            user = User.objects.get(username=new_owner)
            data = {
                      "$class": "org.example.mynetwork.OwnTransaction",
                      "asset": "resource:org.example.mynetwork.MyAsset#%s" %product_id,
                      "newOwner": "resource:org.example.mynetwork.UserParticipant#%s" %new_owner,
                    }

            send_post(api="OwnTransaction", data=data)
            messages.success(request, "Product transfered successfully")
        except User.DoesNotExist:
            logger.error("New owner doesn't exist")
            messages.error(request, "User %s does not exist. Unable to transfer product" %new_owner)
        except:
            logger.error("Error transfering product")
            logger.error(traceback.format_exc())
            messages.error(request, "Unable to transfer product")
        return HttpResponseRedirect(reverse('products'))
    else:
        owner = "?owner=resource%3Aorg.example.mynetwork.UserParticipant%23" + str(request.user.username)
        products_json = send_get(api="queries/selectMyAssetbyUser",param=owner).text
        products = json.loads(products_json)
        return render(request, 'products.html', {'products': products})

@login_required
def check_product_view(request, product_id=None):
    logger.info("[check_product_view]. Product_id-> %s" %product_id)
    context = {}
    if product_id:
        context = get_product_complete_info(product_id)
        if not context:
            messages.error(request, "Product not found in the blockchain")
        if request.is_ajax():
            return JsonResponse(context)
    return render(request, 'check_product.html', context)

@login_required
@registrador_only
def catalog_view(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name', None)
        try:
            product = ProductType.objects.get(name=product_name, registrador=request.user.registrador)

            timestamp = str(datetime.datetime.now().isoformat())
            logger.info("Timestamp -> %s" %timestamp)
            data = {
                    "$class": "org.example.mynetwork.MyAsset",
                    "assetId": id_generator(product, request.user.username),
                    "owner": "resource:org.example.mynetwork.UserParticipant#" + request.user.username,
                    "name": product.name,
                    "description": product.description,
                    "imageUrl": product.img_url,
                    "register": "resource:org.example.mynetwork.UserParticipant#" + request.user.username,
                    "timestamp": timestamp,
                }
            response = send_post(api="MyAsset", data=data)
            if response.status_code == 200:
                messages.success(request, "The product %s was added to the blockchain" %product_name)
            else:
                messages.error(request, "Error while sending product to the blockchain")

        except:
            messages.error(request, "This product is not properly registered")
        return HttpResponseRedirect(reverse('catalog'))
    else:
        product_types = ProductType.objects.filter(registrador=request.user.registrador)
        return render(request, 'catalog.html', {'product_types': product_types})

@login_required
@registrador_only
def register_product_view(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name', None)
        product_description = request.POST.get('product_description', None)
        product_image = request.POST.get('product_image', None)

        try:
            ProductType.objects.get(name=product_name)
            messages.error(request, "There is already a product with the name %s" %(product_name))
            return render(request, 'register_product.html')
        except:
            pass
        new_product_type = ProductType()
        new_product_type.name = product_name
        new_product_type.description = product_description
        new_product_type.img_url = product_image
        new_product_type.registrador = request.user.registrador
        new_product_type.save()
        return HttpResponseRedirect(reverse('catalog'))
    else:
        return render(request, 'register_product.html')

#############
# FUNCTIONS #
#############

base_url = "http://traceit.hyperledger.blocksait.com/api/"

def send_post(api, data):
    logger.info("Sending post to %s" %api)
    response = requests.post(base_url + api, data=data)
    logger.info("Response status: %s" %str(response.status_code))
    logger.info("Response text: %s" %response.text)
    return response

def send_get(api, param=None):
    logger.info("Sending get to %s" %api)
    if param:
        response = requests.get(base_url + api + "/" + param)
    else:
        response = requests.get(base_url + api)

    logger.info("Response status: %s" %str(response.status_code))
    logger.info("Response text: %s" %response.text)
    return response

def id_generator(product_type, registrador_username):
    return product_type.name.replace(' ', '_') + '_' + registrador_username + '_' + str(random.randint(0, 1000000))

def get_product_complete_info(product_id):
    response = send_get(api="MyAsset", param=product_id)
    if response.status_code == 200:
        product_json = response.text
        product = json.loads(product_json)
    else: 
        return None

    owners = []
    owners.append({
                    'owner': participant_to_username(product['register']),
                    'timestamp': product['timestamp']
                })
    param = "?MyAsset=resource%3Aorg.example.mynetwork.MyAsset%23" + product_id
    response = send_get(api="queries/selectOwnTransactionbyMyAsset", param=param)
    if response.status_code == 200:
        transactions_json = response.text
        transactions = json.loads(transactions_json)
        transactions.reverse()
        for t in transactions:
            owners.append({
                'owner': participant_to_username(t['newOwner']),
                'timestamp': t['timestamp']
            })
    return {
            'product': product,
            'owners': owners,
        }


def participant_to_username(participant):
    return participant.split('#')[-1]