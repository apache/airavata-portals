<template>
  <div>
    <div class="flex flex-col items-stretch gap-4 md:flex-row md:items-start">
      <div class="flex-1">
        <Card>
          <CardHeader>
            <CardTitle class="text-base">Gateway Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="mb-4 flex items-center gap-2">
              <FilterIcon class="size-4 text-muted-foreground" />
              <Input
                v-model="userFilter"
                placeholder="Filter list of users"
                @change="onUserFilterChange"
              />
            </div>

            <div class="max-h-80 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="w-8"></TableHead>
                    <TableHead>Username</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <template v-for="item in displayedNonMembers" :key="item.id">
                    <TableRow
                      class="cursor-pointer"
                      :data-state="isUserSelected(item) ? 'selected' : undefined"
                      @click="toggleUserSelection(item)"
                    >
                      <TableCell>
                        <CircleCheckBig
                          v-if="isUserSelected(item)"
                          class="size-4 text-primary"
                        />
                      </TableCell>
                      <TableCell>{{ item.username }}</TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          @click.stop="toggleUserExpansion(item.id)"
                        >
                          {{ expandedUsers[item.id] ? "Hide" : "Show" }} Details
                        </Button>
                      </TableCell>
                    </TableRow>
                    <TableRow v-if="expandedUsers[item.id]" :key="item.id + '-expansion'">
                      <TableCell colspan="3">
                        <group-members-details-container
                          :userProfile="item"
                          :name="item.name"
                          :id="item.id"
                          @change-role="changeRole"
                        />
                      </TableCell>
                    </TableRow>
                  </template>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      <div class="flex flex-row justify-center gap-2 md:flex-col md:justify-start">
        <Button
          size="icon"
          :disabled="selectedUsers.length < 1"
          @click="addSelectedMembers"
          title="Add selected members"
        >
          <ChevronRight class="size-4" />
        </Button>

        <Button
          size="icon"
          :disabled="nonMembers.length < 1"
          @click="showAdd = true"
          title="Add all members"
        >
          <ChevronsRight class="size-4" />
        </Button>

        <Button
          size="icon"
          :disabled="membersCount < 2"
          @click="showRemove = true"
          title="Remove all members"
        >
          <ChevronsLeft class="size-4" />
        </Button>

        <Button
          size="icon"
          :disabled="selectedMembers.length < 1"
          @click="removeSelectedMembers"
          title="Remove selected members"
        >
          <ChevronLeft class="size-4" />
        </Button>

        <Dialog v-model:open="showRemove">
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Are you sure?</DialogTitle>
            </DialogHeader>
            <p class="text-sm">
              Do you really want to remove all members from
              '<strong>{{ group.name }}</strong>'?
            </p>
            <DialogFooter>
              <Button variant="secondary" @click="showRemove = false">No</Button>
              <Button variant="destructive" @click="removeAllMembers">Yes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog v-model:open="showAdd">
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Are you sure?</DialogTitle>
            </DialogHeader>
            <p class="text-sm">
              Do you really want to add all users to
              '<strong>{{ group.name }}</strong>'?
            </p>
            <DialogFooter>
              <Button variant="secondary" @click="showAdd = false">No</Button>
              <Button @click="addAllMembers">Yes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div class="flex-1">
        <Card>
          <CardHeader>
            <CardTitle class="text-base">Group Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="mb-4 flex items-center gap-2">
              <FilterIcon class="size-4 text-muted-foreground" />
              <Input
                v-model="memberFilter"
                placeholder="Filter list of members"
                @change="onMemberFilterChange"
              />
            </div>

            <div v-if="membersCount > 0" class="max-h-80 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="w-8"></TableHead>
                    <TableHead>Username</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <template v-for="item in displayedMembers" :key="item.id">
                    <TableRow
                      class="cursor-pointer"
                      :class="item.isNew ? 'bg-success/10' : ''"
                      :data-state="
                        isMemberSelected(item) ? 'selected' : undefined
                      "
                      @click="toggleMemberSelection(item)"
                    >
                      <TableCell>
                        <CircleCheckBig
                          v-if="isMemberSelected(item)"
                          class="size-4 text-primary"
                        />
                      </TableCell>
                      <TableCell>
                        {{ item.username }}
                        <Badge v-if="item.role == 'OWNER'">Owner</Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          @click.stop="toggleMemberExpansion(item.id)"
                        >
                          {{ expandedMembers[item.id] ? "Hide" : "Show" }}
                          Details
                        </Button>
                      </TableCell>
                    </TableRow>
                    <TableRow
                      v-if="expandedMembers[item.id]"
                      :key="item.id + '-expansion'"
                    >
                      <TableCell colspan="3">
                        <group-members-details-container
                          :userProfile="item"
                          :name="item.name"
                          :id="item.id"
                          :role="item.role"
                          :isOwner="group.is_owner"
                          @change-role="changeRole"
                        />
                      </TableCell>
                    </TableRow>
                  </template>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import GroupMembersDetailsContainer from "./GroupMembersDetailsContainer.vue";
import {
  Filter as FilterIcon,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  CircleCheckBig,
} from "@lucide/vue";

export default {
  name: "group-members-editor",
  components: {
    GroupMembersDetailsContainer,
    FilterIcon,
    ChevronLeft,
    ChevronRight,
    ChevronsLeft,
    ChevronsRight,
    CircleCheckBig,
  },
  props: {
    group: {
      type: models.Group,
      required: true,
    },
  },
  data() {
    return {
      userProfiles: null,
      newMembers: [],
      userFilter: null,
      memberFilter: null,
      selectedMembers: [],
      selectedUsers: [],
      // Per-row expansion state keyed by row id (replaces b-table's
      // toggleExpansion/#row-expansion mechanics).
      expandedUsers: {},
      expandedMembers: {},
      showRemove: false,
      showAdd: false,
    };
  },

  computed: {
    members() {
      return this.group.members ? this.group.members : [];
    },
    admins() {
      return this.group.admins;
    },
    userProfilesMap() {
      if (!this.userProfiles) {
        return null;
      }
      const result = {};
      this.userProfiles.forEach((up) => {
        result[up.airavata_internal_user_id] = up;
      });
      return result;
    },
    currentMembers() {
      if (!this.userProfilesMap) {
        return [];
      }
      return (
        this.members
          // Filter out users that are missing profiles
          .filter((m) => m in this.userProfilesMap)
          .map((m) => {
            const userProfile = this.userProfilesMap[m];
            const isAdmin = this.admins.indexOf(m) >= 0;
            const isOwner = this.group.owner_id === m;
            // Owners can edit all members and admins can edit non-admin members
            // (except the owners role isn't editable)
            const editable =
              !isOwner &&
              (this.group.is_owner || (this.group.is_admin && !isAdmin));
            return {
              id: m,
              name: userProfile.first_name + " " + userProfile.last_name,
              username: userProfile.user_id,
              email: userProfile.email,
              role: isOwner ? "OWNER" : isAdmin ? "ADMIN" : "MEMBER",
              editable: editable,
              isOwner: isOwner,
              // Highlight newly-added members (replaces b-table's _rowVariant).
              isNew: this.newMembers.indexOf(m) >= 0,
            };
          })
      );
    },
    nonMembers(){
      if (!this.userProfiles) {
        return [];
      }
      return (
        this.userProfiles
          // Filter out current members
          .filter(
            (userProfile) =>
              this.group.members.indexOf(userProfile.airavata_internal_user_id) < 0
          )
          .map((userProfile) => {
            return {
              id: userProfile.airavata_internal_user_id,
              name: userProfile.first_name + " " + userProfile.last_name,
              username: userProfile.user_id,
              email: userProfile.email,
            };
          })
      );
    },

    membersCount() {
      return this.members.length;
    },
    // Filtered + sorted rows for the Gateway Users table (b-table previously
    // applied :filter and :sort-compare/:sort-by internally).
    displayedNonMembers() {
      return this.nonMembers
        .filter((u) => this.filterUserProfile(u, this.userFilter))
        .slice()
        .sort((a, b) => this.sortCompare(a, b, "username"));
    },
    // Filtered + sorted rows for the Group Members table.
    displayedMembers() {
      return this.currentMembers
        .filter((m) => this.filterUserProfile(m, this.memberFilter))
        .slice()
        .sort((a, b) => this.sortCompare(a, b, "username"));
    },
  },

  created() {
    services.UserProfileService.list().then((userProfiles) => {
      this.userProfiles = userProfiles;
    });
  },

  watch: {
    // Selecting rows in one table clears the other table's selection (the two
    // tables are mutually exclusive). With bootstrap-vue-next the selection is
    // a controlled v-model:selected-items array rather than ref methods.
    selectedUsers(items) {
      if (items.length > 0 && this.selectedMembers.length > 0) {
        this.selectedMembers = [];
      }
    },
    selectedMembers(items) {
      // The owner row is not removable, so never keep it selected.
      const withoutOwner = items.filter((m) => m.role !== "OWNER");
      if (withoutOwner.length !== items.length) {
        this.selectedMembers = withoutOwner;
        return;
      }
      if (items.length > 0 && this.selectedUsers.length > 0) {
        this.selectedUsers = [];
      }
    },
  },

  methods: {
    isUserSelected(user){
      if (this.selectedUsers.length>0){
        for (let i = 0; i<this.selectedUsers.length;i++){
         if (user==this.selectedUsers[i]){
           return true;
          }
        }
      }
      return false;
    },
    isMemberSelected(member){
      if (this.selectedMembers.length>0){
        for (let i = 0; i<this.selectedMembers.length;i++){
         if (member==this.selectedMembers[i]){
           return true;
          }
        }
      }
      return false;
    },
    // Multi-select toggle on row click (replaces b-table's selectable rows).
    toggleUserSelection(user) {
      const index = this.selectedUsers.indexOf(user);
      if (index >= 0) {
        this.selectedUsers = this.selectedUsers.filter((u) => u !== user);
      } else {
        this.selectedUsers = [...this.selectedUsers, user];
      }
    },
    toggleMemberSelection(member) {
      // The owner row is not removable, so never select it.
      if (member.role === "OWNER") {
        return;
      }
      const index = this.selectedMembers.indexOf(member);
      if (index >= 0) {
        this.selectedMembers = this.selectedMembers.filter((m) => m !== member);
      } else {
        this.selectedMembers = [...this.selectedMembers, member];
      }
    },
    toggleUserExpansion(id) {
      this.expandedUsers = {
        ...this.expandedUsers,
        [id]: !this.expandedUsers[id],
      };
    },
    toggleMemberExpansion(id) {
      this.expandedMembers = {
        ...this.expandedMembers,
        [id]: !this.expandedMembers[id],
      };
    },
    addSelectedMembers(){
      this.selectedUsers.forEach((user)=>  {
        this.newMembers.push(user.id);
        this.$emit("add-member", user.id);
        }
      );
      this.selectedUsers=[];
      this.selectedMembers=[];
    },
    addAllMembers(){
      this.showAdd = false;
      this.selectedUsers = this.nonMembers.filter(
      (user) =>
              this.filterUserProfile(user, this.userFilter)
          ).map((x)=>(x));
      this.addSelectedMembers();
      this.userFilter=null;
      this.memberfilter=null;
    },
    removeSelectedMembers() {
      this.selectedMembers.forEach((member)=>{
         if (member.role == "MEMBER"|| member.role =="ADMIN"){
          this.$emit("remove-member", member.id);
        }});
      this.selectedMembers = [];
      this.selectedUsers=[];
    },
    removeAllMembers(){
      this.showRemove = false;
      this.selectedMembers = this.currentMembers.filter(
      (member) =>
              this.filterUserProfile(member, this.memberFilter)
          ).map((x)=>(x));
      this.removeSelectedMembers();
      this.memberFilter=null;
    },
    onUserFilterChange(){
      this.selectedUsers = [];
    },
    onMemberFilterChange(){
      this.selectedMembers = [];
    },
    changeRole(item) {
      if (item[1] === "ADMIN") {
        this.$emit("change-role-to-admin", item[0]);
      } else {
        this.$emit("change-role-to-member", item[0]);
      }
    },
    filterUserProfile(profile, filter){
      if(filter){
      if (profile.email.toLowerCase().includes(filter.toLowerCase())){
        return true;
      }
      else if(profile.name.toLowerCase().includes(filter.toLowerCase())){
        return true;
      }else if(profile.username.toLowerCase().includes(filter.toLowerCase())){
        return true;
      }else{return false;}
      }else{
        return true;
      }
    },
    sortCompare(aRow, bRow, key) {
      // Sort new members before all others
      const aNewIndex = this.newMembers.indexOf(aRow.id);
      const bNewIndex = this.newMembers.indexOf(bRow.id);
      if (aNewIndex >= 0 && bNewIndex >= 0) {
        return aNewIndex - bNewIndex;
      } else if (aNewIndex >= 0) {
        return -1;
      } else if (bNewIndex >= 0) {
        return 1;
      }
      const a = aRow[key];
      const b = bRow[key];
      if (
        (typeof a === "number" && typeof b === "number") ||
        (a instanceof Date && b instanceof Date)
      ) {
        // If both compared fields are native numbers or both are dates
        return a < b ? -1 : a > b ? 1 : 0;
      } else {
        // Otherwise stringify the field data and use String.prototype.localeCompare
        return new String(a).localeCompare(new String(b));
      }
    },
  },
};
</script>
