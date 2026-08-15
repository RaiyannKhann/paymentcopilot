{{- define "paymentcopilot.name" -}}
paymentcopilot
{{- end -}}

{{- define "paymentcopilot.fullname" -}}
{{ .Release.Name }}-paymentcopilot
{{- end -}}

{{- define "paymentcopilot.labels" -}}
app.kubernetes.io/name: {{ include "paymentcopilot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "paymentcopilot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "paymentcopilot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "paymentcopilot.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{ .Values.serviceAccount.name | default (include "paymentcopilot.fullname" .) }}
{{- else -}}
{{ .Values.serviceAccount.name | default "default" }}
{{- end -}}
{{- end -}}

{{- define "paymentcopilot.secretName" -}}
{{- if .Values.secret.existingSecretName -}}
{{ .Values.secret.existingSecretName }}
{{- else -}}
{{ include "paymentcopilot.fullname" . }}-secret
{{- end -}}
{{- end -}}
