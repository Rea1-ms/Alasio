<script lang="ts">
  import { t } from "$lib/i18n";

  type $Props = {
    // timestamp in seconds or ISO string
    timestamp: number | string;
    class?: string;
  };
  let { timestamp, class: className }: $Props = $props();

  let now = $state(Date.now());
  $effect(() => {
    const interval = setInterval(() => {
      now = Date.now();
    }, 60000); // update every 60s
    return () => clearInterval(interval);
  });

  const displayTime = $derived.by(() => {
    const target = typeof timestamp === "number" ? timestamp * 1000 : new Date(timestamp).getTime();
    const diff = target - now;
    const dayInMs = 24 * 60 * 60 * 1000;

    if (diff <= 0) {
      return t.Scheduler.Now();
    } else if (diff <= dayInMs) {
      // within 24h, display as hh:mm
      const date = new Date(target);
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
    } else {
      return t.Scheduler.Over24Hours();
    }
  });
</script>

<span class={className}>{displayTime}</span>
