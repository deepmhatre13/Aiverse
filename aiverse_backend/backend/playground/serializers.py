from rest_framework import serializers

from .models import Dataset, Experiment, TrainingLog


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'task_type', 'description', 'n_samples', 'n_features']
        read_only_fields = fields


class ExperimentStartSerializer(serializers.Serializer):
    dataset_id = serializers.IntegerField()


class ExperimentSelectModelSerializer(serializers.Serializer):
    model_type = serializers.CharField(max_length=64)


class ExperimentSetHyperparametersSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError('hyperparameters must be an object')
        return data


class TrainingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingLog
        fields = ['epoch', 'loss', 'accuracy', 'timestamp']
        read_only_fields = fields


class ExperimentDetailSerializer(serializers.ModelSerializer):
    dataset = DatasetSerializer(read_only=True)
    logs_stream = serializers.SerializerMethodField()

    class Meta:
        model = Experiment
        fields = [
            'id',
            'dataset',
            'current_step',
            'model_type',
            'hyperparameters',
            'status',
            'metrics',
            'logs',
            'error',
            'logs_stream',
            'created_at',
            'updated_at',
        ]

    def get_logs_stream(self, obj):
        # last 200 epochs for UI graph
        qs = obj.training_logs.all().order_by('epoch')[:200]
        return TrainingLogSerializer(qs, many=True).data
