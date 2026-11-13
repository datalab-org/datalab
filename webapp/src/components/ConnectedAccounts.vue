<template>
  <div class="connected-accounts">
    <div v-if="uniqueIdentities.length" class="d-flex flex-wrap">
      <component
        :is="profileUrl(identity) ? 'a' : 'span'"
        v-for="identity in uniqueIdentities"
        :key="`${identity.identity_type}-${identity.identifier}`"
        class="btn btn-sm mr-2 mb-1 identity-chip"
        :class="{
          'identity-chip-static': !profileUrl(identity),
          'btn-outline-primary identity-chip-primary': isPrimary(identity),
          'btn-outline-secondary': !isPrimary(identity),
        }"
        :href="profileUrl(identity)"
        :target="profileUrl(identity) ? '_blank' : undefined"
        :title="providerFor(identity).label"
      >
        <font-awesome-icon
          :icon="providerFor(identity).icon"
          :class="providerFor(identity).iconClass"
        />
        {{ identity.name }}
        <span v-if="isPrimary(identity)" class="badge badge-primary ml-1">Primary</span>
        <span v-if="!identity.verified" class="badge badge-warning ml-1">Unverified</span>
      </component>
    </div>
    <div v-else class="small text-muted mb-1">
      {{ section === "emails" ? "No email addresses." : "No connected accounts." }}
    </div>

    <div v-if="section === 'accounts' && connectableProviders.length" class="d-flex flex-wrap">
      <a
        v-for="provider in connectableProviders"
        :key="provider.type"
        class="btn btn-sm btn-default mr-2 mb-1"
        :aria-label="`Connect ${provider.label} account`"
        :href="`${apiUrl}/login/${provider.type}`"
      >
        <font-awesome-icon :icon="provider.icon" :class="provider.iconClass" />
        Connect {{ provider.label }}
      </a>
    </div>
  </div>
</template>

<script>
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { API_URL } from "@/resources.js";

// Known identity providers; `connectable` ones can be linked via OAuth from this page
const PROVIDERS = {
  github: {
    label: "GitHub",
    icon: ["fab", "github"],
    connectable: true,
    profileUrl: (identity) => `https://github.com/${identity.name}`,
  },
  orcid: {
    label: "ORCID",
    icon: ["fab", "orcid"],
    iconClass: "orcid-icon",
    connectable: true,
    profileUrl: (identity) => `https://orcid.org/${identity.name}`,
  },
  google: { label: "Google", icon: ["fab", "google"], connectable: true },
  microsoft: { label: "Microsoft", icon: ["fab", "microsoft"], connectable: true },
  email: { label: "Email", icon: ["fa", "envelope"] },
};

const GENERIC_PROVIDER = { icon: ["fa", "link"] };

export default {
  name: "ConnectedAccounts",
  components: { FontAwesomeIcon },
  props: {
    identities: {
      type: Array,
      default: () => [],
    },
    // "emails" shows only email identities; "accounts" shows all others plus connect buttons
    section: {
      type: String,
      default: "accounts",
      validator: (value) => ["accounts", "emails"].includes(value),
    },
    // The user's contact email, shown first and highlighted in the "emails" section
    primaryEmail: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      apiUrl: API_URL,
    };
  },
  computed: {
    uniqueIdentities() {
      // Older accounts may hold duplicate identities; show each once (verified if any copy is)
      const unique = new Map();
      const inSection = (identity) =>
        (identity.identity_type === "email") === (this.section === "emails");
      for (const identity of this.identities.filter(inSection)) {
        const key = `${identity.identity_type}-${identity.identifier}`;
        const existing = unique.get(key);
        unique.set(
          key,
          existing ? { ...existing, verified: existing.verified || identity.verified } : identity,
        );
      }
      // Stable sort that moves the primary email to the front
      return [...unique.values()].sort((a, b) => this.isPrimary(b) - this.isPrimary(a));
    },
    connectableProviders() {
      const enabled = this.$store.state.serverInfo?.features?.auth_mechanisms ?? {};
      const connected = new Set(this.identities.map((identity) => identity.identity_type));
      return Object.entries(PROVIDERS)
        .filter(([type, provider]) => provider.connectable && enabled[type] && !connected.has(type))
        .map(([type, provider]) => ({ type, ...provider }));
    },
  },
  methods: {
    providerFor(identity) {
      return (
        PROVIDERS[identity.identity_type] ?? {
          ...GENERIC_PROVIDER,
          label: identity.identity_type,
        }
      );
    },
    isPrimary(identity) {
      return (
        identity.identity_type === "email" &&
        Boolean(this.primaryEmail) &&
        identity.identifier.toLowerCase() === this.primaryEmail.toLowerCase()
      );
    },
    profileUrl(identity) {
      return this.providerFor(identity).profileUrl?.(identity) ?? null;
    },
  },
};
</script>

<style scoped>
.orcid-icon {
  color: #a6ce39;
}

.identity-chip {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.identity-chip-static,
.identity-chip-static:hover {
  cursor: default;
  color: #6c757d;
  background-color: transparent;
}

.identity-chip-primary.identity-chip-static,
.identity-chip-primary.identity-chip-static:hover {
  color: #007bff;
}
</style>
