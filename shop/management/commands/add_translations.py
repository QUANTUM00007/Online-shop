from django.core.management.base import BaseCommand
from parler.utils.context import switch_language
from shop.models import Product

class Command(BaseCommand):
    help = 'Add translations for products'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        for product in products:
            for language_code in ['es']:  # Add other languages as needed
                with switch_language(product, language_code):
                    if not product.safe_translation_getter('name', None):
                        product.set_current_language(language_code)
                        product.name = f"{product.name} ({language_code})"
                        product.slug = f"{product.slug}-{language_code}"
                        product.description = f"{product.description} ({language_code})"
                        product.save()
        self.stdout.write(self.style.SUCCESS('Successfully added translations for products'))
