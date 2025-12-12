"""Teste de ping para SR Linux usando gNMI."""
from typing import Callable, Dict, Any
import pytest
from nornir.core.task import Result, Task
from nornir_napalm.plugins.tasks import napalm_cli
from nuts.helpers.result import AbstractHostResultExtractor, NutsResult
from nuts.context import NornirNutsContext
import re

class PingExtractor(AbstractHostResultExtractor):
    """Extrai resultado do ping"""
    
    def __init__(self, context):
        super().__init__(context)
        self.test_data_list = context.nuts_parameters.get("test_data", [])
    
    def single_transform(self, single_result) -> Dict[str, Dict[str, Any]]:
        """Transforma TODOS os resultados de ping em um dicionário indexado por destination"""
        results = {}
        
        for idx, result in enumerate(single_result):
            if idx >= len(self.test_data_list):
                continue
                
            destination = self.test_data_list[idx]["destination"]
            output = str(result.result)
            
            # Extrai estatísticas
            packets_transmitted = 0
            packets_received = 0
            
            match = re.search(r'(\d+)\s+packets transmitted,\s+(\d+)\s+received', output.lower())
            if match:
                packets_transmitted = int(match.group(1))
                packets_received = int(match.group(2))
            
            # Determina sucesso
            success = packets_received > 0 if packets_transmitted > 0 else False
            
            results[destination] = {
                "output": output,
                "success": success,
                "packets_transmitted": packets_transmitted,
                "packets_received": packets_received,
                "packet_loss": packets_transmitted - packets_received if packets_transmitted > 0 else 0
            }
        
        return results

class PingContext(NornirNutsContext):
    """Context para executar ping no SR Linux"""
    
    def nuts_task(self) -> Callable[..., Result]:
        return napalm_cli
    
    def nuts_arguments(self) -> Dict[str, Any]:
        """Argumentos para o comando ping"""
        test_data_list = self.nuts_parameters.get("test_data", [])
        
        commands = []
        for data in test_data_list:
            destination = data.get("destination", "127.0.0.1")
            count = data.get("count", 4)
            vrf = data.get("vrf", "default")
            timeout = data.get("timeout", 5)
            
            cmd = f"ping -c {count} -W {timeout} network-instance {vrf} {destination}"
            commands.append(cmd)
        
        return {"commands": commands}
    
    def nuts_extractor(self) -> PingExtractor:
        return PingExtractor(self)

CONTEXT = PingContext

class TestSRLinuxPing:
    """Testes de ping para SR Linux"""
    
    @pytest.mark.nuts("host,destination")
    def test_ping_success(self, single_result: NutsResult, host: str, destination: str) -> None:
        """Verifica se o ping foi bem-sucedido"""
        assert destination in single_result.result, \
            f"Destino {destination} não encontrado nos resultados"
        assert single_result.result[destination]["success"], \
            f"Ping de {host} para {destination} falhou"
    
    @pytest.mark.nuts("host,destination")
    def test_ping_no_loss(self, single_result: NutsResult, host: str, destination: str) -> None:
        """Verifica se não houve perda de pacotes"""
        assert destination in single_result.result, \
            f"Destino {destination} não encontrado nos resultados"
        packet_loss = single_result.result[destination]["packet_loss"]
        assert packet_loss == 0, \
            f"Perda de {packet_loss} pacotes no ping de {host} para {destination}"
    
    @pytest.mark.nuts("host,destination,max_drop")
    def test_ping_max_drop(self, single_result: NutsResult, host: str, destination: str, max_drop: int) -> None:
        """Verifica se a perda está dentro do limite aceitável"""
        assert destination in single_result.result, \
            f"Destino {destination} não encontrado nos resultados"
        packet_loss = single_result.result[destination]["packet_loss"]
        assert packet_loss <= max_drop, \
            f"Perda de {packet_loss} pacotes excede o máximo permitido de {max_drop}"
