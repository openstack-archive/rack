# -*- encoding: utf-8 -*-
lib = File.expand_path('../lib', __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)

Gem::Specification.new do |gem|
  gem.name          = "fluent-plugin-udp_msgpack"
  gem.version       = "0.0.1"
  gem.authors       = ["Tomoya Goto"]
  gem.email         = ["tomoya.goto@ctc-g.co.jp"]
  gem.description   = %q{Receive message from udp and decode with msgpack}
  gem.summary       = %q{Receive message from udp and decode with msgpack. I'm using it to accept openstack-ceilometer metering.}
  gem.homepage      = "https://github.com/stackforge/rack/tree/master/tools"

  gem.files         = `git ls-files`.split($/)
  gem.executables   = gem.files.grep(%r{^bin/}).map{ |f| File.basename(f) }
  gem.test_files    = gem.files.grep(%r{^(test|spec|features)/})
  gem.require_paths = ["lib"]
  gem.add_development_dependency "fluentd"
  gem.add_runtime_dependency "fluentd"
end
