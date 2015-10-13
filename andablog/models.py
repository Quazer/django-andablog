# -*- coding: utf-8 -*-
import time

from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings

from markitup.fields import MarkupField
from model_utils.models import TimeStampedModel
from taggit.managers import TaggableManager


class Entry(TimeStampedModel):
    """
    Represents a blog Entry.
    Uses TimeStampModel to provide created and modified fields
    """
    title = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, editable=False)
    content = MarkupField()
    is_published = models.BooleanField(default=False)
    published_timestamp = models.DateTimeField(blank=True, null=True, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, editable=True)
    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = "entries"

    def get_absolute_url(self):
        return reverse('andablog:entrydetail', args=[self.slug])

    def _slugify_title(self):
        """Slugify the Entry title, but ensure it's less than 50 characters.
        This method also ensures that a slug is unique by appending a timestamp
        to any duplicate slugs.

        """
        # Restrict slugs to 50 chars, but don't split mid-word
        self.slug = slugify(self.title)
        while len(self.slug) > 50:
            self.slug = '-'.join(self.slug.split('-')[:-1])

        # Is the same slug as another entry?
        if Entry.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            # Append time to differentiate, but keep total length < 50 chars.
            timestamp = str(int(time.time()))
            slug = "{}-{}".format(self.slug, timestamp)
            if len(slug) > 50:
                slug = '-'.join([self.slug[:-len(timestamp)], timestamp])
            self.slug = slug

    def save(self, *args, **kwargs):
        self._slugify_title()

        # Time to publish?
        if not self.published_timestamp and self.is_published:
            self.published_timestamp = timezone.now()
        elif not self.is_published:
            self.published_timestamp = None

        super(Entry, self).save(*args, **kwargs)


class EntryImage(TimeStampedModel):
    entry = models.ForeignKey(Entry)
    image = models.ImageField(blank=True, upload_to='andablog/images')

    @property
    def image_url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return self.image.url

    def __unicode__(self):
        return u"{entry} - {image}".format(
            entry=truncatechars(self.entry, 10),
            image=truncatechars(self.image.name, 10),
        )
