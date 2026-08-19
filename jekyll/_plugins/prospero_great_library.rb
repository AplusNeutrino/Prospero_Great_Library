# frozen_string_literal: true
require 'json'

module ProsperoGreatLibrary
  module Filters
    def pgl_hours(minutes)
      return '0' if minutes.nil?
      hours = minutes.to_f / 60.0
      hours >= 100 ? hours.round.to_s : format('%.1f', hours)
    end

    def pgl_rating(value)
      return '' if value.nil?
      format('%.1f', value.to_f).sub(/\.0$/, '')
    end
  end

  module PageTitle
    module_function

    def config_for(site)
      site.config['prospero_great_library'] || site.config['personal_library'] || {}
    end

    def library_page?(page)
      return true if page.data['pgl_library'] == true
      config = config_for(page.site)
      permalink = (config.dig('page', 'permalink') || '/library/').to_s
      page.data['permalink'].to_s == permalink
    end

    def locale_for(site)
      lang = (site.config['lang'] || site.config.dig('prospero_great_library', 'locale') || 'en').to_s
      locales = site.data['pgl_locales'] || {}
      locales[lang] || locales[lang.split('-').first] || locales['en'] || {}
    end

    def render_title(page)
      config = config_for(page.site)
      explicit = config.dig('ui', 'title')
      return explicit.to_s unless explicit.nil? || explicit.to_s.strip.empty?

      site_title = page.site.config['title'].to_s.strip
      locale = locale_for(page.site)
      template = locale['title_template'].to_s
      template = '%{site} Great Library' if template.empty?
      begin
        format(template, site: site_title)
      rescue KeyError, ArgumentError
        "#{site_title} Great Library"
      end
    end
  end
end

Liquid::Template.register_filter(ProsperoGreatLibrary::Filters)

# Chirpy renders page.title as its visible dynamic heading and tab label. Marking
# the installed page with pgl_library lets PGL supply a site-aware default title
# without forking Chirpy layouts. Explicit ui.title always wins.
Jekyll::Hooks.register :pages, :pre_render do |page, _payload|
  next unless ProsperoGreatLibrary::PageTitle.library_page?(page)
  page.data['title'] = ProsperoGreatLibrary::PageTitle.render_title(page)
end
