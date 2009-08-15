import models
from google.appengine.ext.db import djangoforms
from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from django.template import Context, loader


class BlogEntryForm(djangoforms.ModelForm):
  class Meta:
    model = models.BlogEntry
    exclude = ['published', 'images', 'snippets', 'slug', 'comments']
    
class BlogEntryCommentForm(djangoforms.ModelForm):
  class Meta:
    model = models.BlogEntryComment
    exclude = ['published', 'reference']
    
class BlogEntryImageForm(djangoforms.ModelForm):
  class Meta:
    model = models.BlogEntryImage
    exclude = ['image_reference', 'image_blob', 'image_name', 'image_snippet']