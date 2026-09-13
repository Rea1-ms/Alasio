<script lang="ts">
  import WindowControls from "./WindowControls.svelte";

  let { floating = false } = $props();
</script>

{#if floating}
  <!-- Floating mode: the embedded web app provides its own header,
       so only the non-interactive center title and window controls may
       intercept pointer input. The outer overlay must stay transparent to
       clicks or it blocks the iframe's config, language and theme controls. -->
  <div class="pointer-events-none fixed top-0 right-0 left-0 z-100 flex h-12 items-center justify-end select-none">
    <div
      class="pointer-events-auto absolute inset-y-0 right-1/3 left-1/3"
      style="-webkit-app-region: drag"
    ></div>
    <div class="pointer-events-auto">
      <WindowControls />
    </div>
  </div>
{:else}
  <!-- Keep h-12 aligned with AppHeader bottom in the embedded web app -->
  <div class="bg-card border-border z-100 flex h-12 items-center border-b select-none">
    <!-- self-stretch makes the drag region span the full 48px title bar height -->
    <div class="flex flex-1 items-center self-stretch px-4" style="-webkit-app-region: drag">
      <span class="text-sm font-semibold">Alasio</span>
    </div>
    <WindowControls />
  </div>
{/if}
