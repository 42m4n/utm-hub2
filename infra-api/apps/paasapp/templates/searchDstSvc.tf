locals {
  source_ips = ["sh-kube-m1"]
  dest_ips   = ["sh-kube-m3"]
  services   = ["HTTPS","FTP","GRE"]
}

data "fortios_firewall_policylist" "all" {
}

data "fortios_firewall_policy" "policy" {
  for_each = toset([for id in data.fortios_firewall_policylist.all.policyidlist : tostring(id)])
  policyid = each.value
}

locals {
  policies_flattened = {
    for id, policy in data.fortios_firewall_policy.policy :
    id => {
      srcaddr_names = [for src in policy.srcaddr : src.name]
      dstaddr_names = [for dst in policy.dstaddr : dst.name]
      service_names = [for svc in policy.service : svc.name]
    }
  }
  filter_svc_dst = {
    for id, policy in local.policies_flattened :
    id => policy if alltrue([for svc in local.services : contains(policy.service_names, svc)])
    && alltrue([for dip in local.dest_ips : contains(policy.dstaddr_names, dip)])
    && length(policy.dstaddr_names) == length(local.dest_ips)
    && length(policy.service_names) == length(local.services)
  }
  filter_src_dst = {
    for id, policy in local.policies_flattened :
    id => policy if alltrue([for sip in local.source_ips : contains(policy.srcaddr_names, sip)])
    && alltrue([for dip in local.dest_ips : contains(policy.dstaddr_names, dip)])
    && length(policy.srcaddr_names) == length(local.source_ips)
    && length(policy.dstaddr_names) == length(local.dest_ips)
  }
  list_ids = length(local.filter_svc_dst) > 0 ? [for id, policy in local.filter_svc_dst : id] : [for id, policy in local.filter_src_dst : id]
  filtered_policies = {
    for id, policy in data.fortios_firewall_policy.policy :
    id => policy if contains(local.list_ids, id)
  }
  policies_with_changes = {
    for id, policy in local.filtered_policies :
    id => policy if(
      length(local.policies_flattened[id].service_names) != length(policy.service) ||
      length(local.policies_flattened[id].srcaddr_names) != length(policy.srcaddr) ||
      length(local.policies_flattened[id].dstaddr_names) != length(policy.dstaddr)
    )
  }
  anychanges = length(local.policies_with_changes) > 0
}

resource "fortios_firewall_policy" "existing_policy" {
  for_each = local.filtered_policies
  lifecycle {
    prevent_destroy = true
    ignore_changes = [
      dynamic_sort_subtable,
      get_all_tables
    ]
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
  dynamic "service" {
    for_each = local.services
    content {
      name = service.value
    }
  }
  dynamic "srcaddr" {
    for_each = each.value.srcaddr
    content {
      name = srcaddr.value.name
    }
  }
  dynamic "srcaddr" {
    for_each = local.source_ips
    content {
      name = srcaddr.value
    }
  }
  dynamic "dstaddr" {
    for_each = each.value.dstaddr
    content {
      name = dstaddr.value.name
    }
  }
  comments              = local.anychanges ? join("\nupdated with ", [each.value.comments, "new-comment"]) : each.value.comments
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
  to       = fortios_firewall_policy.existing_policy[each.key]
  id       = each.value.policyid
}

resource "fortios_firewall_policy" "new_policy" {
  count    = length(local.filtered_policies) == 0 ? 1 : 0
  name     = "policy1"
  action   = "accept"
  comments = "created for new ticket"
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
  dynamic "service" {
    for_each = local.services
    content {
      name = service.value
    }
  }
}