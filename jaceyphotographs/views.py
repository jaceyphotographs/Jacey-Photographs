from django.http import HttpResponse
from google.appengine.ext.db import djangoforms
from django.core.paginator import Paginator
from django import forms
from google.appengine.ext import db
from models import BlogEntry
from models import BlogEntryComment
from models import BlogEntryImage
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
import jacey_forms
import re
from django.template import RequestContext
from google.appengine.api import users
from django.template.defaultfilters import slugify
import datetime, calendar, time
from django.utils.feedgenerator import Rss201rev2Feed
from os import environ
import urllib
from google.appengine.api import urlfetch
from django.utils import simplejson
from google.appengine.api import mail
import captcha


MONTHS = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12 }
STANDARD_PAGINATION = 5
MAX_PAGINATION = 1000
RECAPTCHA_PRIVATE_KEY = "6LcBIQUAAAAAAD5e6yMgSOgyGJxgB0zMwcWjYpcN"

# Main index view, passes over to helper function
def index(request):
  entries_list = db.Query(BlogEntry).order('-published')
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
# Archive list view
def admin(request):
  entries_list = db.Query(BlogEntry).order('-published')
  return generated_template_response(request, entries_list, 'base_admin.html', MAX_PAGINATION)
  
  
# Hackable URL: tags
def tags(request, tag_name):
  entries_list = db.Query(BlogEntry).order('-published').filter('tags =', tag_name)
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
# About page
def about(request):
  return render_to_response('base_about.html', {}) 
  
# Contact page
def details(request):
  return render_to_response('base_details.html', {})  
  
  
# Serve an image
def serve_image(request):
  key = request.GET.get('id', None)
  image = db.get(db.Key(key))
  response = HttpResponse(image.image_blob, mimetype='image/jpg')
  return response
  
# Hackable URL: slug
def slug(request, slug):
  entries_list = db.Query(BlogEntry).filter('slug =', slug)
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
# Hackable URL: year, month, day
def archive_day(request, year, month, day):  
  published = datetime.date(int(year), MONTHS[month], int(day))
  entries_list = db.Query(BlogEntry).filter('published =', published)
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
  
# Hackable URL: year and month
def archive_month(request, year, month):
  published = datetime.date(int(year), MONTHS[month], 1)
  entries_list = db.Query(BlogEntry).filter('published >=', published).filter('published <=', datetime.date(int(year), MONTHS[month], calendar.mdays[published.month]))
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
# Hackable URL: year only
def archive_year(request, year):
  published = datetime.date(int(year), 1, 1)
  entries_list = db.Query(BlogEntry).filter('published >=', published).filter('published <=', datetime.date(int(year), 12, 31))
  return generated_template_response(request, entries_list, 'base_content.html', STANDARD_PAGINATION)
  
  
# Helper function that takes a list of BlogEntries and returns a rendered response
def generated_template_response(request, entries_list, template_name, desired_pagination):
  images_and_snippets = []
  new_entries_list = []
  comments_list = []
  images_list = []
  for entry in entries_list:
    new_entries_list.append({'key' : entry.key(), 'slug' : entry.getSlug(), 'title' : entry.getTitle(), 'description' : entry.getDescription(), 'tags' : entry.getTags(), 'published' : entry.getPublished(), 'blog_comments' : entry.blogentrycomment_set, 'blog_images' : entry.blogentryimage_set} )
     
  paginator = Paginator(new_entries_list, desired_pagination)
  # Make sure page request is an int. If not, deliver first page.
  try:
    page = int(request.GET.get('page', '1'))
  except ValueError:
    page = 1
   # If page request (9999) is out of range, deliver last page of results.
  try:
    entries = paginator.page(page)
  except (EmptyPage, InvalidPage):
    entries = paginator.page(paginator.num_pages)

  return render_to_response(template_name, {'entries' : entries,})
  
  
# Receives a POST request to add a new BlogEntry, parses and validates it, and inserts the new BlogEntry into the GAE db.
def blog_post(request, key=None,):

  instance = None
  
  if key is not None and key != 'None':
    instance = BlogEntry.objects.get(key)
    
  if request.method == 'POST' and instance is None:
    form = jacey_forms.BlogEntryForm(request.POST)

    if form.is_valid():
      new_blog_entry = form.save(commit=False)
      new_tag_list = [t for t in re.split('[\s,]+', form.cleaned_data['tags']) if t]
      new_tags = []
      # Now add the tags
      for tag_name in new_tag_list:
        tag = unicode(slugify(tag_name))
        new_tags.append(tag_name)
      form.cleaned_data['tags'] = new_tags
      form.cleaned_data['slug'] = unicode(slugify(form.cleaned_data['title']))
      new_blog_entry = form.save()
      
      image_num = 1
      for file in request.FILES:
        image_form = jacey_forms.BlogEntryImageForm(request.POST, file)
        if image_form.is_valid(): 
          new_blog_entry_image = image_form.save(commit=False)
          new_blog_entry_image.image_reference = new_blog_entry
          uploaded_image = request.FILES[file]
          new_blog_entry_image.image_snippet = request.POST.get('image_snippet_' + str(image_num))
          new_blog_entry_image.image_blob = uploaded_image.read()
          new_blog_entry_image.image_name = unicode(uploaded_image.name)
          new_blog_entry_image = image_form.save()
          image_num += 1
      return HttpResponseRedirect('/admin')
    
  elif request.method == 'POST' and instance is not None:
    form = jacey_forms.BlogEntryForm(request.POST, instance=instance)
    if form.is_valid():
      new_blog_entry = form.save(commit=False)
      new_tag_list = [t for t in re.split('[\s,]+', form.cleaned_data['tags']) if t]
      new_tags = []
      # Now add the tags
      for tag_name in new_tag_list:
        tag = unicode(slugify(tag_name))
        new_tags.append(tag_name)
      instance.slug = unicode(slugify(form.cleaned_data['title']))
      instance.tags = new_tags
      instance.description = form.cleaned_data['description']
      instance.put()
    return HttpResponseRedirect('/admin')
      
  else:
    form = jacey_forms.BlogEntryForm(instance=instance)
  
  return render_to_response('base_post.html', {'form' : form, 'key' : key })
  
# Receives a POST request to add a new comment to an existing BlogEntry object, parses and validates it, and inserts the new comment into the BlogEntry object comments list.
def comment_post(request, id=None):
  instance = None
  if id is not None:
    instance = BlogEntryComment.objects.get(id=id)
      
  captcha_response = captcha.submit(request.POST.get("recaptcha_challenge_field", None),  
    request.POST.get("recaptcha_response_field", None),  
    RECAPTCHA_PRIVATE_KEY,  
	request.META.get("REMOTE_ADDR", None))  

  if request.method == 'POST':
    form = jacey_forms.BlogEntryCommentForm(request.POST, instance=instance)
    clean = form.is_valid()
    rdict = {'bad':'false'}
    if not clean:
      rdict.update({'bad':'true'})
      d={}
      for e in form.errors.iteritems():
        d.update({e[0]:unicode(e[1])}) # e[0] is the id, unicode(e[1]) is the error HTML.
        rdict.update({'errs': d  })
    else:
      # look to wrap in transaction
      if captcha_response.is_valid:  
      	new_blog_entry_comment = form.save(commit=False)
      	blog_entry_key = request.POST.get('key', False)
      	blog_entry = db.get(blog_entry_key)
      	new_blog_entry_comment.reference = blog_entry.key()
      	new_blog_entry_comment = form.save()

        # let's send an email to jacey to let her know someone commented
        # TODO: factor this into its own reusable method
        sender_name = request.POST.get('name', False)
        #sender_email = request.POST.get('jacey@jaceyphotographs.com', False)
        sender_email = 'write2dylan@gmail.com'
        sender_subject = 'Someone commented on one of your photos!'
        sender_message = request.POST.get('comment', False)
        mail.send_mail(sender=sender_email,
          to="Jacey <jacey@jaceyphotographs.com>",
          cc="Dylan Lorimer <write2dylan@gmail.com>",
          subject=sender_subject,
          body=sender_message)
      else:
        captcha_error = "&error=%s" % captcha_response.error_code
    if request.is_ajax():
      return HttpResponse(simplejson.dumps(rdict), mimetype='application/javascript')
    else:
      return HttpResponseRedirect('/')
  else:
    form = jacey_forms.BlogEntryForm(instance=instance)

  return render_to_response('base_content.html', rdict, captcha_error)
  
  
  
# Receives a POST request wtih a blog entry key that is to be deleted
def blog_entry_delete(request):
  blog_entry_key = request.POST.get('key', False)
  blog_entry = db.get(blog_entry_key)
  if blog_entry is not None:
    for comment in blog_entry.blogentrycomment_set:
      comment.delete()
    for image in blog_entry.blogentryimage_set:
      image.delete()
    db.delete(blog_entry)
  if request.is_ajax() or request.GET.has_key('xhr'):
      rdict = {'success':'true'}   
      return HttpResponse(simplejson.dumps(rdict), mimetype='application/javascript')
  else:
    return HttpResponseRedirect('/admin')
  
# Receives a POST request with the contents of an email that is to be sent to Jacey.
def email_jacey(request):
  if request.method == 'POST':
    sender_name = request.POST.get('sender_name', False)
    sender_email = request.POST.get('sender_email', False)
    sender_subject = request.POST.get('sender_subject', False)
    sender_message = request.POST.get('sender_message', False)
    mail.send_mail(sender=sender_email,
              to="Jacey Photographs <jacey@jaceyphotographs.com>",
              cc="Dylan Lorimer <write2dylan@gmail.com>",
              subject=sender_subject,
              body=sender_message)
    return HttpResponseRedirect('/')
  return render_to_response('base_contact.html', {})

  
# RSS Feed
# TODO: add categories to the feed?
def rss_feed(request):
  entries_list = db.Query(BlogEntry).order('-published').fetch(10)
  tld = u'http:/www.jaceyphotograhps.com/'
  author_email = 'jacey@jaceyphotographs.com'
  author_name = 'Jane Cosner'
  copyright = 'Copyright Jacey Photographs 2008'
  feed = Rss201rev2Feed( u"Jacey Photographs", tld, u'RSS feed for www.jaceyphotographs.com' )
  bogus_time = datetime.time(12,0,0)
  for entry in entries_list:
    published = entry.getPublished()
    title = entry.getTitle()
    description = entry.getDescription()
    published = entry.getPublished()
    link = tld + published.strftime("%Y/%b/%d/").lower() + entry.getSlug()
    feed.add_item(title=title, link=link, description=description, author_email=author_email, pubdate=datetime.datetime.combine(published, bogus_time))
  response = HttpResponse(mimetype='application/xml')
  feed.write(response, 'utf-8')
  return response
  
# Function returning a sitemap
def sitemap(request):
  response = HttpResponse(mimetype='application/xml')
  response.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
  response.write("<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">")
  #response.write("xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" ")
  #response.write("xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" ")
  #response.write("xsi:schemaLocation=\"http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd\"> ")
  response.write("<url><loc>http://www.jaceyphotographs.com/</loc><priority>1.00</priority><changefreq>daily</changefreq></url> ")
  response.write("<url><loc>http://www.jaceyphotographs.com/about</loc><priority>0.80</priority><changefreq>monthly</changefreq></url>")
  response.write("<url><loc>http://www.jaceyphotographs.com/contact</loc><priority>0.80</priority><changefreq>monthly</changefreq></url>")
  response.write("<url><loc>http://www.jaceyphotographs.com/feed</loc><priority>0.80</priority><changefreq>daily</changefreq></url>")
  response.write("<url><loc>http://www.jaceyphotographs.com/details</loc><priority>0.80</priority><changefreq>monthly</changefreq></url>")
  response.write("</urlset>")
  return response
