<script lang="ts">
  import { untrack } from "svelte";
  import { toast } from "svelte-sonner";
  import RotateCw from "@lucide/svelte/icons/rotate-cw";
  import Smartphone from "@lucide/svelte/icons/smartphone";
  import ArgCardList from "$lib/components/arg/ArgCardList.svelte";
  import type { ArgData, CardData, InfoData } from "$lib/components/arg/utils.svelte";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { t } from "$lib/i18n";
  import { useTopic } from "$lib/ws";

  type DeviceData = Record<string, CardData>;
  type DeviceAction = "RestartGame" | "RestartDevice";

  const topicClient = useTopic<DeviceData>("Device");
  const setRpc = topicClient.rpc();
  const resetRpc = topicClient.rpc();
  const groupResetRpc = topicClient.rpc();
  const actionRpc = topicClient.rpc({ timeout: 15000 });

  function handleEdit(data: ArgData) {
    setRpc.call("set", {
      task: data.task,
      group: data.group,
      arg: data.arg,
      value: data.value,
    });
  }

  function handleReset(data: ArgData) {
    resetRpc.call("reset", {
      task: data.task,
      group: data.group,
      arg: data.arg,
    });
  }

  function handleGroupReset(data: InfoData) {
    groupResetRpc.call("group_reset", { card: data.card });
  }

  function runAction(task: DeviceAction, name: string) {
    actionRpc.call(
      "run_task",
      { task },
      {
        onSuccess: () => toast.success(t.Device.ActionScheduled({ name }), toastOptions),
      },
    );
  }

  const toastOptions = {
    duration: 2000,
    classes: { toast: "mt-10" },
  };

  $effect(() => {
    if (setRpc.successMsg) {
      untrack(() => toast.success(t.Input.ConfigSet(), toastOptions));
    }
  });
  $effect(() => {
    if (resetRpc.successMsg || groupResetRpc.successMsg) {
      untrack(() => toast.success(t.Input.ConfigReset(), toastOptions));
    }
  });
</script>

<div class="min-h-full w-full px-2.5 py-4">
  <Card.Root class="neushadow mx-auto mb-4 max-w-180 gap-3 border-none">
    <Card.Header>
      <Card.Title class="text-2xl font-bold">{t.Device.ActionTitle()}</Card.Title>
      <Card.Description>{t.Device.ActionHelp()}</Card.Description>
    </Card.Header>
    <Card.Content class="flex flex-wrap gap-2">
      <Button
        variant="outline"
        disabled={actionRpc.isPending}
        onclick={() => runAction("RestartGame", t.Device.RestartGame())}
      >
        <RotateCw />
        {t.Device.RestartGame()}
      </Button>
      <Button
        variant="outline"
        disabled={actionRpc.isPending}
        onclick={() => runAction("RestartDevice", t.Device.RestartDevice())}
      >
        <Smartphone />
        {t.Device.RestartDevice()}
      </Button>
    </Card.Content>
  </Card.Root>

  {#if topicClient.data}
    <ArgCardList class="w-full" bind:data={topicClient.data} {handleEdit} {handleReset} {handleGroupReset} />
  {/if}
</div>
