Known Issues
============

Mapping of non-existing Hub configured on new Spoke
---------------------------------------------------
Facing an issue when a Hub is removed from the network but not from the inventory and New Spoke is added to the topology 
,Newly added Spoke is configured with the nhrp static mapping & BGP neighborship of that Hub which was removed
previously(but remains in the inventory)

.. note::

  **Root cause**: As Hubs are added to the inventory the nhs_nbma & nhs_server lists is appended in the 
  Defaults Table and remains there if that Hub is added to the topology or not. When Spokes are configured
  ,configuration template runs a loop around nhs_nbma and nhs_server list and configure static nhrp mapping around it.


Issue with archive directory
----------------------------
When configuring archive feature, Uurnik Connect configure "unix:" directory for archive.

.. note::

  When using in production "unix:" keyword must be changed to appropriate directory,
  as this is done only for testing purposes on Cisco IOU devices.



No error Handling for multiple default routes
---------------------------------------------

.. note::

  if there are multiple static default route on the device , configuration will fail !