module Fluent
  class UDPInput < Fluent::Input
    Plugin.register_input('udpmsgpack', self)
    include DetachMultiProcessMixin
    require 'socket'
    require 'msgpack'
    def initialize
      super
    end

    config_param :port, :integer, :default => 5160
    config_param :body_size_limit, :size, :default => 10240
    config_param :tag, :string, :default => "udp_msgpack"
    config_param :bind, :string, :default => '0.0.0.0'

    def configure(conf)
      super
    end

    def start

      @udp_s = UDPSocket.new


      detach_multi_process do
        super
           @udp_s.bind(@bind, @port)
           $log.debug "listening UDP on #{@bind}:#{@port}"
        @thread = Thread.new(&method(:run))
      end
    end

    def shutdown
      @udp_s.close
      @thread.join
    end
    
    def run
       loop do
         text, sender =  @udp_s.recvfrom(@body_size_limit)
         text = MessagePack::unpack(text)
         Engine.emit(@tag, Engine.now,  text)
       end
    rescue
      $log.error "unexpected error", :error=>$!.to_s
      $log.error_backtrace
    end

  end
end



