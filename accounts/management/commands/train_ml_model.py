from typing import Optional
from django.core.management.base import BaseCommand, CommandError
from ml_services import ProgressPredictor
from accounts.models import GameResult


class Command(BaseCommand):
    help = 'Train ML model for predicting game performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-type',
            type=str,
            default=None,
            help='Specific game type to train on (e.g., math, memory). If not specified, trains on all game types.',
        )
        parser.add_argument(
            '--model-type',
            type=str,
            default='random_forest',
            choices=['linear', 'random_forest'],
            help='Type of ML model to use (default: random_forest)',
        )
        parser.add_argument(
            '--window-size',
            type=int,
            default=3,
            help='Number of past games to use for feature engineering (default: 3)',
        )
        parser.add_argument(
            '--min-entries',
            type=int,
            default=5,
            help='Minimum number of game entries required per user-game combination (default: 5)',
        )
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Fraction of data to use for testing (default: 0.2)',
        )
        parser.add_argument(
            '--all-game-types',
            action='store_true',
            help='Train separate models for each game type',
        )

    def handle(self, *args, **options):
        game_type: Optional[str] = options['game_type']
        model_type: str = options['model_type']
        window_size: int = options['window_size']
        min_entries: int = options['min_entries']
        test_size: float = options['test_size']
        all_game_types: bool = options['all_game_types']

        # Validate game_type if provided
        if game_type:
            valid_game_types = dict(GameResult.GameType.choices).keys()
            if game_type not in valid_game_types:
                raise CommandError(
                    f'Invalid game type "{game_type}". '
                    f'Valid options: {", ".join(valid_game_types)}'
                )

        # Determine which game types to train
        if all_game_types:
            game_types_to_train = [gt[0] for gt in GameResult.GameType.choices]
            self.stdout.write(
                self.style.SUCCESS(
                    f'Training models for all game types: {", ".join(game_types_to_train)}'
                )
            )
        elif game_type:
            game_types_to_train = [game_type]
        else:
            game_types_to_train = [None]

        # Train models
        results = {}
        for gt in game_types_to_train:
            try:
                self.stdout.write(f'\nTraining model for game_type={gt or "all"}...')
                
                # Initialize predictor
                predictor = ProgressPredictor(
                    model_type=model_type,
                    model_dir='ml_models',
                    window_size=window_size,
                )
                
                # Train
                metrics = predictor.train(
                    game_type=gt,
                    test_size=test_size,
                    min_entries=min_entries,
                )
                
                # Save model
                model_path = predictor.save(game_type=gt)
                
                # Display results
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nTraining complete for game_type={gt or "all"}'
                    )
                )
                self.stdout.write(f'  Model type: {model_type}')
                self.stdout.write(f'  Model saved to: {model_path}')
                self.stdout.write(f'  Training samples: {int(metrics["n_samples"])}')
                self.stdout.write(f'  Features: {int(metrics["n_features"])}')
                self.stdout.write('')
                self.stdout.write('  Performance Metrics:')
                self.stdout.write(f'    Train MAE:  {metrics["train_mae"]:.2f}')
                self.stdout.write(f'    Train RMSE: {metrics["train_rmse"]:.2f}')
                self.stdout.write(f'    Train R²:   {metrics["train_r2"]:.3f}')
                self.stdout.write(f'    Test MAE:   {metrics["test_mae"]:.2f}')
                self.stdout.write(f'    Test RMSE:  {metrics["test_rmse"]:.2f}')
                self.stdout.write(f'    Test R²:    {metrics["test_r2"]:.3f}')
                
                results[gt or 'all'] = metrics
                
            except ValueError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'\nFailed to train model for game_type={gt or "all"}: {str(e)}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'\nUnexpected error for game_type={gt or "all"}: {str(e)}'
                    )
                )
                if options['verbosity'] >= 2:
                    import traceback
                    self.stdout.write(traceback.format_exc())

        # Summary
        if results:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully trained {len(results)} model(s)'
                )
            )
            
            # Display average metrics
            if len(results) > 1:
                avg_test_mae = sum(m['test_mae'] for m in results.values()) / len(results)
                avg_test_r2 = sum(m['test_r2'] for m in results.values()) / len(results)
                self.stdout.write('\nAverage Performance:')
                self.stdout.write(f'  Test MAE: {avg_test_mae:.2f}')
                self.stdout.write(f'  Test R²:  {avg_test_r2:.3f}')
            
            self.stdout.write('')
        else:
            raise CommandError('No models were trained successfully')
