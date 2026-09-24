import { useEffect, useRef } from 'react'

export function useNotifications(stats, onPermissionResult) {
  const wasRunning = useRef(false)

  useEffect(() => {
    if (typeof Notification === 'undefined') return

    const wasRunningBefore = wasRunning.current
    const isRunningNow = !!stats.running

    if (wasRunningBefore && !isRunningNow && stats.done > 0) {
      if (Notification.permission === 'granted') {
        try {
          new Notification('MIU BEE · Generation Complete', {
            body: `${stats.done} of ${stats.total} topics generated`,
            icon: '/miu_logo.png',
            tag: 'miu-bee-done'
          })
        } catch (e) {
          console.warn('Notification failed:', e)
        }
      }
    }

    wasRunning.current = isRunningNow
  }, [stats.running, stats.done, stats.total])

  const requestPermission = async () => {
    if (typeof Notification === 'undefined') return false
    if (Notification.permission === 'granted') return true
    if (Notification.permission === 'denied') return false
    try {
      const result = await Notification.requestPermission()
      onPermissionResult?.(result)
      return result === 'granted'
    } catch {
      return false
    }
  }

  return {
    supported: typeof Notification !== 'undefined',
    granted: typeof Notification !== 'undefined' && Notification.permission === 'granted',
    permission: typeof Notification !== 'undefined' ? Notification.permission : 'unsupported',
    requestPermission
  }
}