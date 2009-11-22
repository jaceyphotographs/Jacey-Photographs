from appengine_django.models import BaseModel
from google.appengine.ext import db

class BlogEntry(BaseModel):  
  published = db.DateTimeProperty(auto_now_add=True)
  title = db.StringProperty(required=True)
  tags = db.StringListProperty()
  description = db.TextProperty()
  comments = db.StringListProperty()
  slug = db.StringProperty()
    
  def getPublished(self):
    return self.published
    
  def getTitle(self):
    return self.title
    
  def getSlug(self):
    return self.slug
    
  def getTags(self):
    return self.tags
    
  def getComments(self):
    return self.comments
    
  def getDescription(self):
    return self.description
    
class BlogEntryComment(BaseModel):  
  published = db.DateTimeProperty(auto_now_add=True)
  name = db.StringProperty(required=True)
  email = db.StringProperty()
  comment = db.TextProperty()
  reference = db.ReferenceProperty(BlogEntry)
  
class BlogEntryImage(BaseModel):  
  image_snippet = db.TextProperty()
  image_name = db.StringProperty()
  image_reference = db.ReferenceProperty(BlogEntry)
  image_blob = db.BlobProperty()
  
  def get_absolute_url(self):
    return "/images?id=%s" %self.key()
