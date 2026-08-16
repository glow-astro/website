# Build the site with Jekyll, bypassing RubyGems' recursive dependency
# activation. See tools/preview.sh for why. Usage:
#
#   ruby tools/jekyll_build.rb <source-dir> <destination-dir>

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

site = Jekyll::Site.new(
  Jekyll.configuration("source" => source, "destination" => dest)
)
site.process

puts "Built #{site.pages.size} pages -> #{dest}"
