# Build the site with Jekyll, bypassing RubyGems' recursive dependency
# activation. See tools/preview.sh for why. Usage:
#
#   ruby tools/jekyll_build.rb <source-dir> <destination-dir> [extra-config...]
#
# Extra config files are overlaid on _config.yml, left to right, later winning
# -- the mechanism Jekyll's own `--config a,b` uses. One exists:
# _config.review.yml, for the access-controlled review host (see §11 of
# docs/SITE_CONVENTIONS.md).
#
# SITE_URL in the environment overrides `url:` from every config file. The
# review host's address is not known until the Pages project exists and would
# go stale in a file, so tools/deploy_review.sh derives it and passes it here.
# Left unset, nothing changes and the build is exactly as it was.

gem_root = File.expand_path("~/.local/share/gem/ruby/#{RUBY_VERSION.sub(/\.\d+$/, '.0')}/gems")

unless Dir.exist?(gem_root)
  abort "No user gem directory at #{gem_root}.\n" \
        "Install Jekyll first, e.g.:\n" \
        "  gem install --user-install jekyll jekyll-sitemap --ignore-dependencies"
end

Dir[File.join(gem_root, "*", "lib")].each { |d| $LOAD_PATH.unshift(d) }

begin
  require "jekyll"
rescue LoadError => e
  abort "Could not load Jekyll from #{gem_root}: #{e.message}"
end

source = ARGV[0] || Dir.pwd
dest   = ARGV[1] || File.join(source, "_site")
extra  = ARGV[2..] || []

overrides = { "source" => source, "destination" => dest }

# Jekyll resolves config paths against the working directory, not the source,
# so expand them here: `ruby tools/jekyll_build.rb . _site _config.review.yml`
# should mean the same thing from anywhere.
unless extra.empty?
  overrides["config"] =
    [File.join(source, "_config.yml")] +
    extra.map { |f| File.expand_path(f, source) }
end

# Overrides beat config files, so this wins over _config.review.yml too.
site_url = ENV["SITE_URL"]
overrides["url"] = site_url unless site_url.to_s.empty?

site = Jekyll::Site.new(Jekyll.configuration(overrides))
site.process

puts "Built #{site.pages.size} pages -> #{dest}"
puts "  url: #{site.config['url']}" if site_url || !extra.empty?
