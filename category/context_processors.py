from .models import Category


# Will be available to be called from any template
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)