from kubernetes import client, config

class KubeClient:
    """A simple Kubernetes client to interact with the cluster."""
    
    def __init__(self):
        try:
            config.load_kube_config()
            self.api_client = client.ApiClient()
            self.core_v1_api = client.CoreV1Api(self.api_client)
            self.apps_v1_api = client.AppsV1Api(self.api_client)
            self.ingress_v1_api = client.NetworkingV1Api(self.api_client)
            self.events_1_api = client.EventsV1Api(self.api_client)
        except Exception as e:
            print(f"Warning: Failed to connect to Kubernetes cluster: {e}")

    async def aconnect(self):
        """Async initialization method"""
        try:
            config.load_kube_config()
            self.api_client = client.ApiClient()
            self.core_v1_api = client.CoreV1Api(self.api_client)
            self.apps_v1_api = client.AppsV1Api(self.api_client)
            self.networking_v1_api = client.NetworkingV1Api(self.api_client)
            self.events_1_api = client.EventsV1Api(self.api_client)
        except Exception as e:
            print(f"Warning: Failed to connect to Kubernetes cluster: {e}")
        return self

    def _get_resource_mapping(self):
        """Get mapping of resource kinds to API clients and method base names."""
        return {
            # Core resources
            "pod": (self.core_v1_api, "pod"),
            "service": (self.core_v1_api, "service"),
            "configmap": (self.core_v1_api, "config_map"),
            "secret": (self.core_v1_api, "secret"),
            "namespace": (self.core_v1_api, "namespace"),
            "persistentvolumeclaim": (self.core_v1_api, "persistent_volume_claim"),
            "persistentvolume": (self.core_v1_api, "persistent_volume"),
            "serviceaccount": (self.core_v1_api, "service_account"),
            "node": (self.core_v1_api, "node"),
            
            # Apps resources
            "deployment": (self.apps_v1_api, "deployment"),
            "replicaset": (self.apps_v1_api, "replica_set"),
            "statefulset": (self.apps_v1_api, "stateful_set"),
            "daemonset": (self.apps_v1_api, "daemon_set"),
            
            # Networking resources
            "ingress": (self.networking_v1_api, "ingress"),
            "ingressclass": (self.networking_v1_api, "ingress_class"),
            "networkpolicy": (self.networking_v1_api, "network_policy"),
            
            # Events resources
            "event": (self.events_1_api, "event"),
        }
    
    def _normalize_resource_kind(self, resource_kind):
        """Normalize resource kind (handle plurals and case)."""
        resource_kind = resource_kind.lower()
        resources = self._get_resource_mapping()
        
        # Handle plural forms
        if resource_kind.endswith('s') and resource_kind not in resources:
            resource_kind = resource_kind[:-1]
            
        return resource_kind
    
    def _get_api_client_and_resource_type(self, resource_kind):
        """Get the API client and resource type for a given resource kind."""
        resource_kind = self._normalize_resource_kind(resource_kind)
        resources = self._get_resource_mapping()
        
        if resource_kind not in resources:
            return None, None
            
        return resources[resource_kind]
    
    def get_resource_types(self):
        """Get all resource types available in the Kubernetes cluster."""
        try:
            resources = self.core_v1_api.get_api_resources()
            return [resource.kind for resource in resources.resources]
        except Exception as e:
            print(f"Error getting resource types: {e}")
            return []
    
    def get_resources(self, resource_kind: str, namespace: str = None):
        """Get resources by kind, similar to 'kubectl get <resource>'"""
        resource_kind = self._normalize_resource_kind(resource_kind)
        api_client, resource_type = self._get_api_client_and_resource_type(resource_kind)
        
        if not api_client or not resource_type:
            return []  # Return empty list for unsupported resource

        print(f"Getting {resource_kind} from {namespace if namespace else 'all namespaces'}")
        
        try:
            # Choose appropriate method based on namespace
            if namespace and resource_kind != "namespace":
                method_name = f"list_namespaced_{resource_type}"
                result = getattr(api_client, method_name)(namespace=namespace)
            else:
                # Try all namespaces method first
                try:
                    method_name = f"list_{resource_type}_for_all_namespaces"
                    result = getattr(api_client, method_name)()
                except AttributeError:
                    # Fallback to regular list method (for resources that don't have namespaces)
                    method_name = f"list_{resource_type}"
                    result = getattr(api_client, method_name)()
            
            # Convert items to serializable dictionaries
            serializable_items = []
            for item in result.items:
                # Use the API client's serialization method to convert to dict
                item_dict = self.api_client.sanitize_for_serialization(item)
                serializable_items.append(item_dict)
            return serializable_items
        except Exception as e:
            print(f"Error getting {resource_kind}: {e}")
            return []  # Return empty list on error

    def describe_resource(self, resource_kind: str, resource_name: str, namespace: str = "default"):
        """
        Get detailed information about a specific resource.
        Similar to 'kubectl describe <resource_type> <resource_name>'
        """
        resource_kind = self._normalize_resource_kind(resource_kind)
        api_client, resource_type = self._get_api_client_and_resource_type(resource_kind)
        
        if not api_client or not resource_type:
            return {"error": f"Unsupported resource kind: {resource_kind}"}

        print(f"Describing {resource_kind} {resource_name} in namespace {namespace}")
        
        try:
            # Choose appropriate method - most resources use read_namespaced_*
            if resource_kind != "namespace":
                method_name = f"read_namespaced_{resource_type}"
                result = getattr(api_client, method_name)(name=resource_name, namespace=namespace)
            else:
                # Namespaces aren't namespaced
                method_name = f"read_{resource_type}"
                result = getattr(api_client, method_name)(name=resource_name)
            
            # Convert to serializable dictionary
            resource_dict = self.api_client.sanitize_for_serialization(result)
            return resource_dict
        except Exception as e:
            print(f"Error describing {resource_kind} {resource_name}: {e}")
            return {"error": f"Failed to describe {resource_kind} {resource_name}: {str(e)}"}
    
    def get_pod_logs(self, pod_name: str, container: str = None, namespace: str = "default"):
        """Get logs from a pod, similar to 'kubectl logs <pod_name>'"""
        try:
            logs = self.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container
            )
            return logs
        except Exception as e:
            print(f"Error getting logs for pod {pod_name}: {e}")
            return f"Failed to get logs: {str(e)}"
            
    def get_pod_logs(self, pod_name: str, container: str = None, namespace: str = "default", tail_lines: int = 100):
        """Get logs from a pod, similar to 'kubectl logs <pod_name>'"""
        try:
            logs = self.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                pretty=True,
                tail_lines=tail_lines,
            )
            return logs
        except Exception as e:
            print(f"Error getting logs for pod {pod_name}: {e}")
            return f"Failed to get logs: {str(e)}"
    