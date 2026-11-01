import os


def volume(action,level=None):
    import comtypes
    from pycaw.pycaw import AudioUtilities
    comtypes.CoInitialize()
    try:
        endpoint=AudioUtilities.GetSpeakers().EndpointVolume
        current=round(endpoint.GetMasterVolumeLevelScalar()*100)
        if action=='status':
            return {'status':'ok','volume':current,'muted':bool(endpoint.GetMute()),'message':f'Computer volume is {current} percent.'}
        if action=='mute':
            endpoint.SetMute(1,None)
        elif action=='unmute':
            endpoint.SetMute(0,None)
        else:
            target=int(level) if action=='set_volume' and level is not None else current+(10 if action=='volume_up' else -10)
            target=max(0,min(100,target))
            endpoint.SetMasterVolumeLevelScalar(target/100,None)
            endpoint.SetMute(0,None)
        final=round(endpoint.GetMasterVolumeLevelScalar()*100)
        return {'status':'ok','volume':final,'muted':bool(endpoint.GetMute()),'message':'Computer sound is muted.' if endpoint.GetMute() else f'Computer volume is {final} percent.'}
    finally:
        comtypes.CoUninitialize()


def control(action,level=None):
    if action in ('wifi_settings','bluetooth_settings'):
        target={'wifi_settings':'ms-settings:network-wifi','bluetooth_settings':'ms-settings:bluetooth'}[action]
        os.startfile(target)
        return {'status':'ok','message':('Wi-Fi' if action=='wifi_settings' else 'Bluetooth')+' settings are open. Use the Windows switch there to change the connection.'}
    if action not in ('status','volume_up','volume_down','set_volume','mute','unmute'):
        raise ValueError('Unknown Windows control.')
    return volume(action,level)
