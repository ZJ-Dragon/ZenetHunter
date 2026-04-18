"""Device identity heuristics shared by backend workflows."""

from __future__ import annotations

from app.models.device import DeviceType


def guess_device_type(
    *,
    ip: str | None,
    vendor: str | None = None,
    model: str | None = None,
    gateway_ip: str | None = None,
) -> DeviceType:
    """Infer a coarse device type from the best available backend signals."""
    if ip and gateway_ip and ip == gateway_ip:
        return DeviceType.ROUTER

    vendor_lower = (vendor or "").lower()
    model_lower = (model or "").lower()
    combined = f"{vendor_lower} {model_lower}".strip()

    router_keywords = [
        "router",
        "modem",
        "gateway",
        "access point",
        "switch",
        "hub",
        "wifi router",
        "wireless router",
    ]
    if model_lower and any(keyword in model_lower for keyword in router_keywords):
        return DeviceType.ROUTER

    mobile_keywords = [
        "iphone",
        "ipad",
        "ipod",
        "galaxy",
        "redmi",
        "honor",
        "phone",
        "tablet",
        "mobile",
        "smartphone",
        "mate",
        "nova",
        "reno",
        "find",
    ]
    if model_lower and any(keyword in model_lower for keyword in mobile_keywords):
        return DeviceType.MOBILE

    mobile_vendors = {
        "apple",
        "samsung",
        "xiaomi",
        "redmi",
        "huawei",
        "honor",
        "oppo",
        "vivo",
        "oneplus",
        "lg",
        "meizu",
    }
    if vendor_lower in mobile_vendors and not any(
        router_word in combined
        for router_word in ["router", "modem", "gateway", "switch"]
    ):
        return DeviceType.MOBILE

    pc_keywords = [
        "laptop",
        "notebook",
        "desktop",
        "pc",
        "computer",
        "macbook",
        "thinkpad",
        "ideapad",
        "zenbook",
        "vivobook",
        "rog",
        "alienware",
        "optiplex",
        "precision",
        "elitebook",
        "probook",
        "pavilion",
        "envy",
        "omen",
        "spectre",
        "zbook",
        "workstation",
        "imac",
        "mac pro",
        "mac mini",
    ]
    if any(keyword in combined for keyword in pc_keywords):
        return DeviceType.PC

    iot_keywords = [
        "iot",
        "homepod",
        "airpods",
        "watch",
        "band",
        "camera",
        "sensor",
        "scale",
        "lock",
        "purifier",
        "vacuum",
        "tv",
        "monitor",
        "printer",
        "scanner",
    ]
    if any(keyword in combined for keyword in iot_keywords):
        return DeviceType.IOT

    return DeviceType.UNKNOWN
