import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AttackManager:
    def __init__(self):
        self.active_attacks = {}
        self.stop_events = {}
    
    def start_sms_attack(self, attack_id, target, count, delay, bomber_instance, message="Security test alert"):
        """Start SMS bombing in a background thread"""
        stop_event = threading.Event()
        self.stop_events[attack_id] = stop_event
        
        def _run():
            sent_count = 0
            for i in range(count):
                if stop_event.is_set():
                    logger.info(f"Attack {attack_id} stopped by user")
                    break
                
                bomber_instance.send(target, message)
                sent_count += 1
                
                if i < count - 1:
                    time.sleep(delay)
            
            self.active_attacks.pop(attack_id, None)
            self.stop_events.pop(attack_id, None)
        
        thread = threading.Thread(target=_run, daemon=True)
        self.active_attacks[attack_id] = {
            'thread': thread,
            'target': target,
            'type': 'sms',
            'started': datetime.now().isoformat(),
            'status': 'running'
        }
        thread.start()
        return attack_id
    
    def start_call_attack(self, attack_id, target, count, delay, bomber_instance, message=None):
        """Start call bombing in a background thread"""
        stop_event = threading.Event()
        self.stop_events[attack_id] = stop_event
        
        def _run():
            sent_count = 0
            for i in range(count):
                if stop_event.is_set():
                    logger.info(f"Attack {attack_id} stopped by user")
                    break
                
                bomber_instance.call(target, message)
                sent_count += 1
                
                if i < count - 1:
                    time.sleep(delay)
            
            self.active_attacks.pop(attack_id, None)
            self.stop_events.pop(attack_id, None)
        
        thread = threading.Thread(target=_run, daemon=True)
        self.active_attacks[attack_id] = {
            'thread': thread,
            'target': target,
            'type': 'call',
            'started': datetime.now().isoformat(),
            'status': 'running'
        }
        thread.start()
        return attack_id
    
    def start_combined_attack(self, attack_id, target, count, delay, sms_bomber, call_bomber, message="Security test alert"):
        """Run both SMS and call attacks alternating"""
        stop_event = threading.Event()
        self.stop_events[attack_id] = stop_event
        
        def _run():
            for i in range(count):
                if stop_event.is_set():
                    break
                
                sms_bomber.send(target, message)
                time.sleep(delay)
                
                if stop_event.is_set():
                    break
                    
                call_bomber.call(target, message)
                time.sleep(delay)
            
            self.active_attacks.pop(attack_id, None)
            self.stop_events.pop(attack_id, None)
        
        thread = threading.Thread(target=_run, daemon=True)
        self.active_attacks[attack_id] = {
            'thread': thread,
            'target': target,
            'type': 'combined',
            'started': datetime.now().isoformat(),
            'status': 'running'
        }
        thread.start()
        return attack_id
    
    def stop_attack(self, attack_id):
        """Stop a running attack"""
        if attack_id in self.stop_events:
            self.stop_events[attack_id].set()
            return True
        return False
    
    def get_active_attacks(self):
        return self.active_attacks
