# If you update this file, please follow
# https://suva.sh/posts/well-documented-makefiles

.DEFAULT_GOAL := help

TAG ?=
GO=go
PACKAGE = $(shell go list -m)
GIT_COMMIT_HASH = $(shell git rev-parse HEAD)
GIT_VERSION = $(shell git describe --tags --always --dirty)
BUILD_TIME = $(shell date -u '+%Y-%m-%dT%H:%M:%SZ')
BINARY_NAME = slack-mcp-server
LD_FLAGS = -s -w \
	-X '$(PACKAGE)/pkg/version.CommitHash=$(GIT_COMMIT_HASH)' \
	-X '$(PACKAGE)/pkg/version.Version=$(GIT_VERSION)' \
	-X '$(PACKAGE)/pkg/version.BuildTime=$(BUILD_TIME)' \
	-X '$(PACKAGE)/pkg/version.BinaryName=$(BINARY_NAME)'
COMMON_BUILD_ARGS = -ldflags "$(LD_FLAGS)"

NPM_VERSION = $(shell git describe --tags --always | sed 's/^v//' | cut -d- -f1)
OSES = darwin linux windows
ARCHS = amd64 arm64

CLEAN_TARGETS :=
CLEAN_TARGETS += '$(BINARY_NAME)'
CLEAN_TARGETS += $(foreach os,$(OSES),$(foreach arch,$(ARCHS),./build/$(BINARY_NAME)-$(os)-$(arch)$(if $(findstring windows,$(os)),.exe,)))
CLEAN_TARGETS += $(foreach os,$(OSES),$(foreach arch,$(ARCHS),./npm/$(BINARY_NAME)-$(os)-$(arch)/bin/))
CLEAN_TARGETS += $(foreach os,$(OSES),$(foreach arch,$(ARCHS),./extension.dxt/server/$(BINARY_NAME)-$(os)-$(arch)))
CLEAN_TARGETS += ./npm/slack-mcp-server/.npmrc ./npm/slack-mcp-server/LICENSE ./npm/slack-mcp-server/README.md
CLEAN_TARGETS += $(foreach os,$(OSES),$(foreach arch,$(ARCHS),./npm/$(BINARY_NAME)-$(os)-$(arch)/.npmrc))

# The help will print out all targets with their descriptions organized bellow their categories. The categories are represented by `##@` and the target descriptions by `##`.
# The awk commands is responsible to read the entire set of makefiles included in this invocation, looking for lines of the file as xyz: ## something, and then pretty-format the target and help. Then, if there's a line with ##@ something, that gets pretty-printed as a category.
# More info over the usage of ANSI control characters for terminal formatting: https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info over awk command: http://linuxcommand.org/lc3_adv_awk.php
#
# Notice that we have a little modification on the awk command to support slash in the recipe name:
# origin: /^[a-zA-Z_0-9-]+:.*?##/
# modified /^[a-zA-Z_0-9\/\.-]+:.*?##/
.PHONY: help
help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9\/\.-]+:.*?##/ { printf "  \033[36m%-21s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: clean
clean: ## Clean up all build artifacts
	rm -rf $(CLEAN_TARGETS)

.PHONY: build
build: clean tidy format ## Build the project
	go build $(COMMON_BUILD_ARGS) -o ./build/$(BINARY_NAME) ./cmd/slack-mcp-server

.PHONY: build-all-platforms
build-all-platforms: clean tidy format ## Build the project for all platforms
	$(foreach os,$(OSES),$(foreach arch,$(ARCHS), \
		GOOS=$(os) GOARCH=$(arch) go build $(COMMON_BUILD_ARGS) -o ./build/$(BINARY_NAME)-$(os)-$(arch)$(if $(findstring windows,$(os)),.exe,) ./cmd/slack-mcp-server; \
	))

.PHONY: build-dxt
build-dxt: ## Build DTX extension
	$(foreach os,$(OSES),$(foreach arch,$(ARCHS), \
		EXECUTABLE=$(BINARY_NAME)-$(os)-$(arch)$(if $(findstring windows,$(os)),.exe,); \
		DIRNAME=$(BINARY_NAME)-$(os)-$(arch); \
		cp ./build/$$EXECUTABLE ./extension.dxt/server/; \
	))
	cp npm/slack-mcp-server/bin/index.js ./extension.dxt/server/
	chmod +x extension.dxt/server/slack-mcp-server-*
	dxt pack extension.dxt/ build/slack-mcp-server-${NPM_VERSION}.dxt
	cp build/slack-mcp-server-${NPM_VERSION}.dxt build/slack-mcp-server.dxt

.PHONY: npm-copy-binaries
npm-copy-binaries: build-all-platforms ## Copy the binaries to each npm package
	$(foreach os,$(OSES),$(foreach arch,$(ARCHS), \
		EXECUTABLE=$(BINARY_NAME)-$(os)-$(arch)$(if $(findstring windows,$(os)),.exe,); \
		DIRNAME=$(BINARY_NAME)-$(os)-$(arch); \
		mkdir -p ./npm/$$DIRNAME/bin; \
		cp ./build/$$EXECUTABLE ./npm/$$DIRNAME/bin/; \
	))

.PHONY: npm-publish
npm-publish: npm-copy-binaries ## Publish the npm packages
	$(foreach os,$(OSES),$(foreach arch,$(ARCHS), \
		DIRNAME="$(BINARY_NAME)-$(os)-$(arch)"; \
		cd npm/$$DIRNAME; \
		echo '//registry.npmjs.org/:_authToken=$(NPM_TOKEN)' >> .npmrc; \
		jq '.version = "$(NPM_VERSION)"' package.json > tmp.json && mv tmp.json package.json; \
		npm publish; \
		cd ../..; \
	))
	cp README.md LICENSE ./npm/slack-mcp-server/
	echo '//registry.npmjs.org/:_authToken=$(NPM_TOKEN)' >> ./npm/slack-mcp-server/.npmrc
	jq '.version = "$(NPM_VERSION)"' ./npm/slack-mcp-server/package.json > tmp.json && mv tmp.json ./npm/slack-mcp-server/package.json; \
	jq '.optionalDependencies |= with_entries(.value = "$(NPM_VERSION)")' ./npm/slack-mcp-server/package.json > tmp.json && mv tmp.json ./npm/slack-mcp-server/package.json; \
	cd npm/slack-mcp-server && npm publish

.PHONY: deps
deps: ## Download dependencies
	$(GO) mod download

.PHONY: test
test: ## Run the tests
	$(GO) test -count=1 -v -run=".*Unit.*" ./...

.PHONY: test-integration
test-integration: ## Run integration tests
	$(GO) test -count=1 -v -run=".*Integration.*" ./...

.PHONY: format
format: ## Format the code
	$(GO) fmt ./...

.PHONY: tidy
tidy: ## Tidy up the go modules
	$(GO) mod tidy

.PHONY: release
release: ## Create release tag. Usage: make tag TAG=v1.2.3
	@if [ -z "$(TAG)" ]; then \
	  echo "Usage: make tag TAG=vX.Y.Z"; exit 1; \
	fi
	git tag -a "$(TAG)" -m "Release $(TAG)"
	git push origin "$(TAG)"
