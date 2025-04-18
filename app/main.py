from mcp.server.fastmcp import FastMCP
from kube_client import KubeClient
from dataclasses import dataclass
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from mcp.server.fastmcp import Context, FastMCP

@dataclass
class AppContext:
    kubeClient: KubeClient

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    print("Initializing Kubernetes client...")
    kube_client = await KubeClient().aconnect()
    
    try:
        # Yield the context to the application
        yield AppContext(kubeClient=kube_client)
    finally:
        # Cleanup on shutdown
        print("Cleaning up resources...")

# Create MCP server with proper configuration
mcp = FastMCP("d6r", dependencies=["kubernetes"], kube_config_path="~/.kube/config", lifespan=app_lifespan)


@mcp.tool(name="resource_types", description="Get all resource types")
def get_resource_kinds(ctx: Context) -> str:
    """Get all resource types available in the Kubernetes cluster."""
    resource_types = ctx.request_context.lifespan_context.kubeClient.get_resource_types()
    return f"Resource types: {', '.join(resource_types)}"


@mcp.tool(name="get_resources", description="Get list of specific resources")
async def get_resources(ctx: Context, resource_kind: str, namespace: str = "") -> list:
    """Get a list of resources by kind, similar to 'kubectl get <resource>'"""
    resources = ctx.request_context.lifespan_context.kubeClient.get_resources(resource_kind, namespace=namespace)
    if not resources:
        return f"No {resource_kind} resources found" + (f" in namespace {namespace}" if namespace else "")
    return resources


@mcp.tool(name="describe_resource", description="Describe a specific resource")
def describe_resource(ctx: Context, resource_kind: str, resource_name: str, namespace: str = "default") -> list:
    """Get detailed information about a specific resource."""
    resource_details = ctx.request_context.lifespan_context.kubeClient.describe_resource(resource_kind, resource_name, namespace=namespace)
    return resource_details


@mcp.tool(name="get_pod_logs", description="Get logs for a specific pod")
async def get_pod_logs(ctx: Context, pod_name: str, namespace: str = "default", tail_lines: int = 100) -> list:
    """Get logs for a specific pod."""
    return ctx.request_context.lifespan_context.kubeClient.get_pod_logs(pod_name, namespace=namespace, tail_lines=tail_lines)