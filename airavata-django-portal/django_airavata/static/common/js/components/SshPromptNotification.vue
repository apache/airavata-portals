<template>
  <div class="ssh-prompts">
    <div v-for="prompt in activePrompts" :key="prompt.session_id" class="ssh-prompt-toast">
      <div class="ssh-prompt-toast__header">
        <i class="fa fa-terminal me-1"></i>
        <strong>SSH Authentication</strong>
      </div>
      <div class="ssh-prompt-toast__body">
        <div class="mb-2 text-muted" style="font-size: 0.8125rem">{{ prompt.hostname }}</div>
        <div class="mb-2">{{ prompt.prompt }}</div>
        <div v-if="prompt.waiting" class="text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i>Authenticating...
        </div>
        <div v-else class="d-flex gap-2">
          <input
            v-model="prompt.response"
            class="form-control form-control-sm"
            :type="prompt.echo === false ? 'password' : 'text'"
            placeholder="Enter response..."
            @keydown.enter="submitResponse(prompt)"
          />
          <button class="btn btn-primary btn-sm" @click="submitResponse(prompt)">Send</button>
        </div>
      </div>
    </div>
    <div
      v-for="result in results"
      :key="result.session_id"
      class="ssh-prompt-toast"
      :class="result.success ? 'ssh-prompt-toast--success' : 'ssh-prompt-toast--error'"
    >
      <div class="ssh-prompt-toast__body">
        <i
          :class="
            result.success ? 'fa fa-check-circle text-success' : 'fa fa-times-circle text-danger'
          "
          class="me-1"
        ></i>
        {{ result.message }}
        <a
          v-if="!result.success"
          href="#"
          class="ms-2"
          style="font-size: 0.75rem"
          @click.prevent="dismissResult(result.session_id)"
          >dismiss</a
        >
      </div>
    </div>
  </div>
</template>

<script>
import { utils } from "django-airavata-api";

export default {
  name: "SshPromptNotification",
  data() {
    return {
      activePrompts: [],
      results: [],
    };
  },
  mounted() {
    if (utils.SSEClient) {
      utils.SSEClient.on("ssh_prompt", this.onSshPrompt);
      utils.SSEClient.on("ssh_result", this.onSshResult);
    }
  },
  beforeUnmount() {
    if (utils.SSEClient) {
      utils.SSEClient.off("ssh_prompt", this.onSshPrompt);
      utils.SSEClient.off("ssh_result", this.onSshResult);
    }
  },
  methods: {
    onSshPrompt(event) {
      const existing = this.activePrompts.find((p) => p.session_id === event.session_id);
      if (existing) {
        existing.prompt = event.prompt;
        existing.echo = event.echo;
        existing.waiting = false;
        existing.response = "";
      } else {
        this.activePrompts.push({
          session_id: event.session_id,
          hostname: event.hostname || "",
          prompt: event.prompt,
          echo: event.echo,
          response: "",
          waiting: false,
        });
      }
    },
    onSshResult(event) {
      this.activePrompts = this.activePrompts.filter((p) => p.session_id !== event.session_id);
      this.results.push({
        session_id: event.session_id,
        success: event.success,
        message: event.message,
      });
      if (event.success) {
        setTimeout(() => {
          this.results = this.results.filter((r) => r.session_id !== event.session_id);
        }, 3000);
      }
    },
    async submitResponse(prompt) {
      prompt.waiting = true;
      try {
        await utils.FetchUtils.post("/api/ssh/respond/", {
          session_id: prompt.session_id,
          response: prompt.response,
        });
      } catch (e) {
        prompt.waiting = false;
      }
    },
    dismissResult(session_id) {
      this.results = this.results.filter((r) => r.session_id !== session_id);
    },
  },
};
</script>

<style scoped>
.ssh-prompts {
  position: fixed;
  top: 60px;
  right: 20px;
  z-index: 10001;
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ssh-prompt-toast {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.ssh-prompt-toast__header {
  padding: 8px 12px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.8125rem;
}
.ssh-prompt-toast__body {
  padding: 10px 12px;
  font-size: 0.875rem;
}
.ssh-prompt-toast--success {
  border-left: 3px solid #10b981;
}
.ssh-prompt-toast--error {
  border-left: 3px solid #ef4444;
}
</style>
