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
end

Liquid::Template.register_filter(ProsperoGreatLibrary::Filters)
