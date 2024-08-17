locals {
  source_ips = ["sh-kube-m2"]
  dest_ips   = ["sh-kube-m1"]
  service    = "pr8000"
}
locals {
  # Flatten policies to extract srcaddr and dstaddr names
  policies_flattened = {
    for id, policy in data.fortios_firewall_policy.policy :
    id => {
      srcaddr_names = [for src in policy.srcaddr : src.name]
      dstaddr_names = [for dst in policy.dstaddr : dst.name]
    }
  }
  # Filter policies based on source and destination IPs
  filtered_flattened = {
    for id, policy in local.policies_flattened :
    id => policy if alltrue([for sip in local.source_ips : contains(policy.srcaddr_names, sip)])
    && alltrue([for dip in local.dest_ips : contains(policy.dstaddr_names, dip)])
    && length(policy.srcaddr_names) == length(local.source_ips)
    && length(policy.dstaddr_names) == length(local.dest_ips)
  }
  # List of filtered policy IDs
  list_ids = [for id, policy in local.filtered_flattened : id]
  # Final filtered policies
  filtered_policies = {
    for id, policy in data.fortios_firewall_policy.policy :
    id => policy if contains(local.list_ids, id)
  }
}

data "fortios_firewall_policylist" "all" {
}

data "fortios_firewall_policy" "policy" {
  for_each = toset([for id in data.fortios_firewall_policylist.all.policyidlist : tostring(id)])
  policyid = each.value
}

resource "fortios_firewall_policy" "xxx" {
  for_each = local.filtered_policies
  lifecycle {
    prevent_destroy = true
  }
  policyid = each.value.policyid
  name     = each.value.name
  dynamic "dstintf" {
    for_each = each.value.dstintf
    content {
      name = dstintf.value.name
    }
  }
  dynamic "srcintf" {
    for_each = each.value.srcintf
    content {
      name = srcintf.value.name
    }
  }
  dynamic "service" {
    for_each = each.value.service
    content {
      name = service.value.name
    }
  }
  dynamic "srcaddr" {
    for_each = each.value.srcaddr
    content {
      name = srcaddr.value.name
    }
  }
  dynamic "dstaddr" {
    for_each = each.value.dstaddr
    content {
      name = dstaddr.value.name
    }
  }
  service {
    name = local.service
  }
  comments              = each.value.comments
  action                = each.value.action
  status                = each.value.status
  schedule              = each.value.schedule
  nat                   = each.value.nat
  av_profile            = each.value.av_profile
  webfilter_profile     = each.value.webfilter_profile
  dnsfilter_profile     = each.value.dnsfilter_profile
  ips_sensor            = each.value.ips_sensor
  application_list      = each.value.application_list
  file_filter_profile   = each.value.file_filter_profile
  ssl_ssh_profile       = each.value.ssl_ssh_profile
  wccp                  = each.value.wccp
  captive_portal_exempt = each.value.captive_portal_exempt
  logtraffic            = each.value.logtraffic
  capture_packet        = each.value.capture_packet
  ippool                = each.value.ippool
}

import {
  for_each = local.filtered_policies
  to       = fortios_firewall_policy.xxx[each.key]
  id       = each.value.policyid
}

resource "fortios_firewall_policy" "new_policy" {
  count  = length(local.filtered_policies) == 0 ? 1 : 0
  name   = "newpolicy"
  action = "accept"
  srcintf {
    name = "port1"
  }
  dstintf {
    name = "port1"
  }
  dynamic "srcaddr" {
    for_each = local.source_ips
    content {
      name = srcaddr.value
    }
  }
  dynamic "dstaddr" {
    for_each = local.dest_ips
    content {
      name = dstaddr.value
    }
  }
  service {
    name = local.service
  }
}