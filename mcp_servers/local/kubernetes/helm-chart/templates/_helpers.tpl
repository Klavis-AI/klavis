{{/*
Expand the name of the chart.
*/}}
{{- define "mcp-server-kubernetes.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mcp-server-kubernetes.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mcp-server-kubernetes.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mcp-server-kubernetes.labels" -}}
helm.sh/chart: {{ include "mcp-server-kubernetes.chart" . }}
{{ include "mcp-server-kubernetes.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Common annotations
*/}}
{{- define "mcp-server-kubernetes.annotations" -}}
{{- with .Values.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mcp-server-kubernetes.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mcp-server-kubernetes.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mcp-server-kubernetes.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mcp-server-kubernetes.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the appropriate init container image based on provider with architecture support
*/}}
{{- define "mcp-server-kubernetes.initImage" -}}
{{- $baseImage := "" }}
{{- if eq .Values.kubeconfig.provider "aws" }}
{{- $baseImage = "amazon/aws-cli" }}
{{- else if eq .Values.kubeconfig.provider "gcp" }}
{{- $baseImage = "gcr.io/google.com/cloudsdktool/cloud-sdk" }}
{{- else if eq .Values.kubeconfig.provider "url" }}
{{- $baseImage = "curlimages/curl" }}
{{- else if eq .Values.kubeconfig.provider "custom" }}
{{- $baseImage = "alpine" }}
{{- else }}
{{- $baseImage = "alpine" }}
{{- end }}
{{- if and .Values.image.architectures .Values.image.architecture }}
{{- $archTag := index .Values.image.architectures .Values.image.architecture | default "latest" }}
{{- printf "%s:%s" $baseImage $archTag }}
{{- else }}
{{- printf "%s:latest" $baseImage }}
{{- end }}
{{- end }}

{{/*
Determine if we need an init container
*/}}
{{- define "mcp-server-kubernetes.needsInitContainer" -}}
{{- if or (eq .Values.kubeconfig.provider "aws") (eq .Values.kubeconfig.provider "gcp") (eq .Values.kubeconfig.provider "url") (eq .Values.kubeconfig.provider "custom") -}}
true
{{- else -}}
false
{{- end -}}
{{- end }}

{{/*
Generate kubeconfig environment variable based on provider
*/}}
{{- define "mcp-server-kubernetes.kubeconfigEnv" -}}
{{- if eq .Values.kubeconfig.provider "url" -}}
  {{- $files := list -}}
  {{- range .Values.kubeconfig.url.configs -}}
    {{- $files = append $files (printf "/kubeconfig/%s.yaml" .name) -}}
  {{- end -}}
  {{- $files | join ":" -}}
{{- else if eq .Values.kubeconfig.provider "content" -}}
  /kubeconfig/kubeconfig.yaml
{{- else if eq .Values.kubeconfig.provider "serviceaccount" -}}
  {{- /* ServiceAccount mode doesn't need KUBECONFIG env var */ -}}
{{- else -}}
  /kubeconfig/kubeconfig
{{- end -}}
{{- end }}

{{/*
Generate architecture-aware node selector
*/}}
{{- define "mcp-server-kubernetes.nodeSelector" -}}
{{- $nodeSelector := .Values.nodeSelector | default dict }}
{{- if .Values.image.architecture }}
{{- $nodeSelector = merge $nodeSelector (dict "kubernetes.io/arch" .Values.image.architecture) }}
{{- end }}
{{- if $nodeSelector }}
{{- toYaml $nodeSelector }}
{{- end }}
{{- end }}

{{/*
Generate architecture-aware affinity
*/}}
{{- define "mcp-server-kubernetes.affinity" -}}
{{- $affinity := .Values.affinity | default dict }}
{{- if and .Values.image.architectures (not .Values.image.architecture) }}
{{- $archList := keys .Values.image.architectures }}
{{- if not (hasKey $affinity "nodeAffinity") }}
{{- $affinity = merge $affinity (dict "nodeAffinity" dict) }}
{{- end }}
{{- if not (hasKey $affinity.nodeAffinity "preferredDuringSchedulingIgnoredDuringExecution") }}
{{- $preferred := list (dict "weight" 100 "preference" (dict "matchExpressions" (list (dict "key" "kubernetes.io/arch" "operator" "In" "values" $archList)))) }}
{{- $affinity = merge $affinity (dict "nodeAffinity" (merge $affinity.nodeAffinity (dict "preferredDuringSchedulingIgnoredDuringExecution" $preferred))) }}
{{- end }}
{{- end }}
{{- if $affinity }}
{{- toYaml $affinity }}
{{- end }}
{{- end }}

{{/*
Get the image tag with architecture support
*/}}
{{- define "mcp-server-kubernetes.imageTag" -}}
{{- if and .Values.image.architectures .Values.image.architecture }}
{{- index .Values.image.architectures .Values.image.architecture | default (.Values.image.tag | default "latest") }}
{{- else }}
{{- .Values.image.tag | default "latest" }}
{{- end }}
{{- end }}

{{/*
Generate health check for TCP port
*/}}
{{- define "mcp-server-kubernetes.tcpSocketCheck" -}}
{{- $values := . }}
{{- if or (eq $values.transport.mode "sse") (eq $values.transport.mode "http") }}
tcpSocket:
  port: {{ $values.transport.service.targetPort | default 3001 }}
{{- else }}
exec:
  command:
  - "/bin/sh"
  - "-c"
  - "pgrep -f 'node.*dist/index.js' > /dev/null"
{{- end }}
{{- end }}

{{/*
Generate health check command based on mode
*/}}
{{- define "mcp-server-kubernetes.healthCheckCommand" -}}
{{- $probe := index . 0 }}
{{- $values := index . 1 }}
{{- if $values.healthChecks.enabled }}
{{- if eq $values.healthChecks.mode "custom" }}
{{- if eq $probe "startup" }}
{{- toYaml $values.healthChecks.customChecks.startup }}
{{- else if eq $probe "liveness" }}
{{- toYaml $values.healthChecks.customChecks.liveness }}
{{- else if eq $probe "readiness" }}
{{- toYaml $values.healthChecks.customChecks.readiness }}
{{- end }}
{{- else }}
- "/bin/sh"
- "-c"
- "pgrep -f 'node.*dist/index.js' > /dev/null"
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate startup probe configuration
*/}}
{{- define "mcp-server-kubernetes.startupProbe" -}}
{{- if .Values.startupProbe.enabled }}
{{- if and (not .Values.startupProbe.exec) (not .Values.startupProbe.httpGet) (not .Values.startupProbe.tcpSocket) }}
{{- include "mcp-server-kubernetes.tcpSocketCheck" .Values | nindent 0 }}
initialDelaySeconds: {{ .Values.startupProbe.initialDelaySeconds | default 10 }}
periodSeconds: {{ .Values.startupProbe.periodSeconds | default 10 }}
timeoutSeconds: {{ .Values.startupProbe.timeoutSeconds | default 5 }}
failureThreshold: {{ .Values.startupProbe.failureThreshold | default 30 }}
successThreshold: {{ .Values.startupProbe.successThreshold | default 1 }}
{{- else }}
{{- omit .Values.startupProbe "enabled" | toYaml }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate liveness probe configuration
*/}}
{{- define "mcp-server-kubernetes.livenessProbe" -}}
{{- if .Values.livenessProbe.enabled }}
{{- if and (not .Values.livenessProbe.exec) (not .Values.livenessProbe.httpGet) (not .Values.livenessProbe.tcpSocket) }}
{{- include "mcp-server-kubernetes.tcpSocketCheck" .Values | nindent 0 }}
initialDelaySeconds: {{ .Values.livenessProbe.initialDelaySeconds | default 30 }}
periodSeconds: {{ .Values.livenessProbe.periodSeconds | default 10 }}
timeoutSeconds: {{ .Values.livenessProbe.timeoutSeconds | default 5 }}
failureThreshold: {{ .Values.livenessProbe.failureThreshold | default 3 }}
successThreshold: {{ .Values.livenessProbe.successThreshold | default 1 }}
{{- else }}
{{- omit .Values.livenessProbe "enabled" | toYaml }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate readiness probe configuration
*/}}
{{- define "mcp-server-kubernetes.readinessProbe" -}}
{{- if .Values.readinessProbe.enabled }}
{{- if and (not .Values.readinessProbe.exec) (not .Values.readinessProbe.httpGet) (not .Values.readinessProbe.tcpSocket) }}
{{- include "mcp-server-kubernetes.tcpSocketCheck" .Values | nindent 0 }}
initialDelaySeconds: {{ .Values.readinessProbe.initialDelaySeconds | default 5 }}
periodSeconds: {{ .Values.readinessProbe.periodSeconds | default 5 }}
timeoutSeconds: {{ .Values.readinessProbe.timeoutSeconds | default 5 }}
failureThreshold: {{ .Values.readinessProbe.failureThreshold | default 3 }}
successThreshold: {{ .Values.readinessProbe.successThreshold | default 1 }}
{{- else }}
{{- omit .Values.readinessProbe "enabled" | toYaml }}
{{- end }}
{{- end }}
{{- end }}