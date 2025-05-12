from django.shortcuts import render, HttpResponse
from .models import Product as WebProduct, Categorie
from dashboard.models import Product as DashboardProduct
from .forms import SearchForm

#
def index(request):
    if request.method == 'POST':
        pcode = request.POST['pcode']
        if Product.objects.filter(pcode=pcode).exists():
            product = Product.objects.get(pcode=pcode)
            product.pseen += 1
            product.save()

            if product.pseen == 1:
                ip = "5.75.198.32" #get_client_ip(request)
                location_data = get_location(ip)
                user_agent = get_user_agent(request)
                print("#######################3")

                user_info = {
                    'ip_address': ip,
                    'is_mobile': user_agent.is_mobile,
                    'is_tablet': user_agent.is_tablet,
                    'is_pc': user_agent.is_pc,
                    'is_bot': user_agent.is_bot,
                    'browser': user_agent.browser.family,
                    'browser_version': user_agent.browser.version_string,
                    'os': user_agent.os.family,
                    'os_version': user_agent.os.version_string,
                    'device_family': user_agent.device.family,
                    'country_short': location_data.get('countryCode', 'Unknown'),
                    'country': location_data.get('country', 'Unknown'),
                    'region': location_data.get('regionName', 'Unknown'),
                    'city': location_data.get('city', 'Unknown'),
                    'latitude': location_data.get('lat', 'Unknown'),
                    'longitude': location_data.get('lon', 'Unknown')
                }

                user_info_instance = UserInfo.objects.create(**user_info)
                product.user_info = user_info_instance
                product.save()

                context = {'product': product}
                return render(request=request, template_name='certificate.html', context=context)
            else:
                return render(request=request, template_name='used.html')
        else:
            return render(request=request, template_name='404.html')
    else:
        context = {'form': SearchForm()}
        return render(request, 'index.html', context)

