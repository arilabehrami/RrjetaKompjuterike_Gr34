import threading
import time
from collections import defaultdict
import json
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Monitor:
    def __init__(self, stats_file_path='monitoring/server_stats.txt', update_interval=5, timeout_seconds=60):
        """
        update_interval: sa sekonda te rregullta per te shkruar stats ne file
        timeout_seconds: nese klienti nuk dergon mesazh per kete kohe -> konsidero timeout
        """
        self.stats_file_path = stats_file_path
        self.update_interval = update_interval
        self.timeout_seconds = timeout_seconds

       
        self.lock = threading.Lock()
       
        self.clients = {}
        self.total_bytes = 0
        self.total_messages = 0

        
        self.running = False
        self._writer_thread = None
        self._timeout_thread = None

   
    def register(self, socket_id, addr):
        """Thirret kur server pranon nje klient (accept()). socket_id = id(socket) ose ndonje unike"""
        with self.lock:
            self.clients[socket_id] = {
                'addr': addr,
                'last_active': time.time(),
                'msg_count': 0,
                'bytes': 0
            }

    def unregister(self, socket_id):
        """Thirret kur socket mbyllet normalisht"""
        with self.lock:
            if socket_id in self.clients:
                del self.clients[socket_id]

    def record_received(self, socket_id, byte_count):
        """Thirret sa here server merr te dhena nga klienti"""
        with self.lock:
            info = self.clients.get(socket_id)
            if info:
                info['last_active'] = time.time()
                info['msg_count'] += 1
                info['bytes'] += byte_count
            self.total_bytes += byte_count
            self.total_messages += 1

    def get_stats_snapshot(self):
        """Kthen nje snapshot te statistikes (kopje)"""
        with self.lock:
            clients_copy = {k: dict(v) for k, v in self.clients.items()}
            return {
                'timestamp': time.time(),
                'num_active_connections': len(self.clients),
                'clients': clients_copy,
                'total_bytes': self.total_bytes,
                'total_messages': self.total_messages
            }

    
    def start(self, close_callback=None):
        """Starton threads: writer + timeout checker.
           close_callback: funksion(socket_id) -> server duhet te mbyll socket-in;
           nese None: monitor do thote listën e socket_id-ve që janë timeout dhe pret që server t'i mbyllë.
        """
        self.running = True
        self._close_callback = close_callback
        self._writer_thread = threading.Thread(target=self._periodic_write_loop, daemon=True)
        self._timeout_thread = threading.Thread(target=self._timeout_loop, daemon=True)
        self._writer_thread.start()
        self._timeout_thread.start()
        logging.info("Monitor started (update_interval=%s, timeout=%s)", self.update_interval, self.timeout_seconds)

    def stop(self):
        self.running = False
        if self._writer_thread:
            self._writer_thread.join(timeout=1)
        if self._timeout_thread:
            self._timeout_thread.join(timeout=1)
        logging.info("Monitor stopped.")

    def _periodic_write_loop(self):
        while self.running:
            self._write_stats_file()
            time.sleep(self.update_interval)

    def _write_stats_file(self):
        snapshot = self.get_stats_snapshot()
       
        try:
            with open(self.stats_file_path, 'w', encoding='utf-8') as f:
                
                serializable = {
                    'timestamp': snapshot['timestamp'],
                    'num_active_connections': snapshot['num_active_connections'],
                    'total_bytes': snapshot['total_bytes'],
                    'total_messages': snapshot['total_messages'],
                    'clients': {
                        str(k): v for k, v in snapshot['clients'].items()
                    }
                }
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logging.exception("Error writing stats file: %s", e)

    def _timeout_loop(self):
        while self.running:
            now = time.time()
            to_timeout = []
            with self.lock:
                for sock_id, info in list(self.clients.items()):
                    if now - info['last_active'] > self.timeout_seconds:
                        to_timeout.append(sock_id)
            
            for sock_id in to_timeout:
                logging.info("Client %s timed out (no activity for %s sec)", sock_id, self.timeout_seconds)
                if self._close_callback:
                    try:
                        self._close_callback(sock_id)
                    except Exception:
                        logging.exception("Error when calling close_callback for %s", sock_id)
                else:
                   
                    self.unregister(sock_id)
            time.sleep(1)

    
    def print_stats_to_console(self):
        snap = self.get_stats_snapshot()
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(snap['timestamp']))
        print("=== SERVER STATS ===")
        print("Timestamp:", ts)
        print("Active connections:", snap['num_active_connections'])
        print("Total messages:", snap['total_messages'])
        print("Total bytes:", snap['total_bytes'])
        print("Per-client:")
        for sock_id, info in snap['clients'].items():
            print(f"  {sock_id} - {info['addr']} - msgs={info['msg_count']} bytes={info['bytes']} last_active={time.ctime(info['last_active'])}")
        print("====================")

    def admin_console_loop(self):
        """Run this in a separate thread if you want to use terminal commands like STATS"""
        while self.running:
            try:
                cmd = input().strip().upper()
            except EOFError:
                break
            if cmd == 'STATS':
                self.print_stats_to_console()
            elif cmd == 'QUIT' or cmd == 'EXIT':
                print("Shkruaj STOP në server për të ndalur.")
               
            else:
                print("Komanda e panjohur. Shkruaj STATS për statistika.")
