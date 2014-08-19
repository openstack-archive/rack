# Msgpack decoder from udp message for Fluentd

This plugin receives messages from udp and decode it with Msgpack.
I'm using it to decode OpenStack Ceilometer metering information and pass it to elasticsearch.


## Installation

Put ruby file to plugin directory
Gemfile will be made pretty soon, so you can install it with `gem`

    cp fluent-plugin-udp_msgpack.rb /etc/td-agent/plugin/


## Configuration

 * `port`
 * `bind`
 * `body_size_limit`
 * `tag`


## Example

    <source>
     type udpmsgpack
     port 10000
     bind 0.0.0.0
     body_size_limit 1m
     tag ceilometer_meter
    </source>


## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request

