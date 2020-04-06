.DEFAULT_GOAL := help

.PHONY: securedrop-rebuild
securedrop-rebuild: ## Rebuilds SecureDrop kernels from source tarball.
# Not using `molecule converge` since we can't also use `vars_prompt`
# to ask for the source tarball.
	@molecule create -s securedrop-rebuild
	@ansible-playbook -vv --diff molecule/securedrop-rebuild/playbook.yml \
		-i molecule/securedrop-rebuild/.molecule/ansible_inventory.yml

.PHONY: securedrop-core
securedrop-core: ## Builds kernels for SecureDrop servers
	molecule converge -s securedrop-docker

.PHONY: securedrop-workstation
securedrop-workstation: ## Builds kernels for SecureDrop Workstation VMs
	molecule converge -s workstation

.PHONY: help
help: ## Prints this message and exits.
	@printf "Subcommands:\n\n"
	@perl -F':.*##\s+' -lanE '$$F[1] and say "\033[36m$$F[0]\033[0m : $$F[1]"' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
