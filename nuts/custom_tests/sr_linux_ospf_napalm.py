"""Teste de OSPF neighbors para SR Linux usando CLI."""
from typing import Callable, Dict, Any
import pytest
from nornir.core.task import Result
from nornir_napalm.plugins.tasks import napalm_cli
from nuts.helpers.result import AbstractHostResultExtractor, NutsResult
from nuts.context import NornirNutsContext
import ast

class OSPFNeighborExtractor(AbstractHostResultExtractor):
    """Extrai informações dos neighbors OSPF"""
    
    def __init__(self, context):
        super().__init__(context)
        self.test_data_list = context.nuts_parameters.get("test_data", [])
    
    def single_transform(self, single_result) -> Dict[str, Dict[str, Any]]:
        """Transforma o resultado do show OSPF neighbors em um dicionário indexado por router_id"""
        
        result_data = single_result[0].result
        neighbors = {}
        
        # Se for string, converte para dict
        if isinstance(result_data, str):
            result_data = ast.literal_eval(result_data)
        
        # Navega pela estrutura do SR Linux
        for cmd, cmd_result in result_data.items():
            if 'instances' in cmd_result:
                for instance in cmd_result['instances']:
                    if 'neighbors_brief' in instance:
                        for neighbor in instance['neighbors_brief']:
                            router_id = neighbor.get('Rtr Id')
                            interface = neighbor.get('Interface-Name')
                            state = neighbor.get('State')
                            priority = neighbor.get('Pri', 1)
                            retx_queue = neighbor.get('RetxQ', 0)
                            dead_timer = neighbor.get('Time Before Dead', 0)
                            
                            neighbors[router_id] = {
                                "interface": interface,
                                "router_id": router_id,
                                "state": state,
                                "priority": priority,
                                "retransmit_queue": retx_queue,
                                "dead_timer": dead_timer,
                                "is_full": state.lower() == "full"
                            }
        
        return neighbors

class OSPFNeighborContext(NornirNutsContext):
    """Context para verificar neighbors OSPF no SR Linux"""
    
    def nuts_task(self) -> Callable[..., Result]:
        return napalm_cli
    
    def nuts_arguments(self) -> Dict[str, Any]:
        """Argumentos para o comando show OSPF neighbors"""
        test_data_list = self.nuts_parameters.get("test_data", [])
        
        if not test_data_list:
            instance = "main"
        else:
            instance = test_data_list[0].get("instance", "main")
        
        cmd = f"show network-instance default protocols ospf instance {instance} neighbor"
        
        return {"commands": [cmd]}
    
    def nuts_extractor(self) -> OSPFNeighborExtractor:
        return OSPFNeighborExtractor(self)

CONTEXT = OSPFNeighborContext

class TestSRLinuxOSPFNeighbor:
    """Testes de OSPF neighbors para SR Linux"""
    
    @pytest.mark.nuts("host,neighbor_id")
    def test_neighbor_exists(self, single_result: NutsResult, host: str, neighbor_id: str) -> None:
        """Verifica se o neighbor OSPF existe"""
        assert neighbor_id in single_result.result, \
            f"Neighbor {neighbor_id} não encontrado no host {host}. Neighbors disponíveis: {list(single_result.result.keys())}"
    
    @pytest.mark.nuts("host,neighbor_id")
    def test_neighbor_state_full(self, single_result: NutsResult, host: str, neighbor_id: str) -> None:
        """Verifica se o neighbor está no estado Full"""
        assert neighbor_id in single_result.result, \
            f"Neighbor {neighbor_id} não encontrado"
        
        neighbor = single_result.result[neighbor_id]
        assert neighbor["is_full"], \
            f"Neighbor {neighbor_id} não está Full. Estado atual: {neighbor['state']}"
    
    @pytest.mark.nuts("host,neighbor_id,expected_interface")
    def test_neighbor_interface(self, single_result: NutsResult, host: str, neighbor_id: str, expected_interface: str) -> None:
        """Verifica se o neighbor está na interface esperada"""
        assert neighbor_id in single_result.result, \
            f"Neighbor {neighbor_id} não encontrado"
        
        neighbor = single_result.result[neighbor_id]
        assert neighbor["interface"] == expected_interface, \
            f"Neighbor {neighbor_id} está em {neighbor['interface']}, esperado {expected_interface}"
