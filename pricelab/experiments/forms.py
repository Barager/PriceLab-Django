from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import Experiment, User, Test
import random
import pandas as pd
from django.db.models import ManyToManyRel, Min, Max, Q
from sklearn.model_selection import StratifiedShuffleSplit


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column


class MetaInfoForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = ['name', 'description', 'owner', 'business_sponsor', 'start_date', 'duration_days']
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
            'description': forms.Textarea(attrs={'autocomplete': 'off'}),
            'owner': forms.TextInput(attrs={'autocomplete': 'off'}),
            'business_sponsor': forms.TextInput(attrs={'autocomplete': 'off'}),
            
        }

class SegmentationForm(forms.ModelForm):
    class Meta:
        model = Experiment
        fields = [] #'criteria_field', 'criteria', 'filter_field', 'filter']
        widgets = {
            'treatment_size': forms.NumberInput(attrs={'step': 0.1, 'min': 0.0, 'max': 1.0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_fields = [
            (field.name, field.verbose_name)
            for field in User._meta.get_fields()
            if hasattr(field, 'verbose_name') and field.name != 'id' and not isinstance(field, ManyToManyRel)
        ]
        
        for field_name, field_label in self.user_fields:
            if field_name == 'customer_uuid':
                # Exclude customer_uuid from the form
                continue
            elif field_name == 'location_title':
                all_choices = User.objects.values_list(field_name, field_name).distinct()
                print(f"All Choices for {field_name}: {all_choices}")

                # Define a list of location titles to filter out
                titles_to_exclude = ['Amsterdam temp', 'Launch temp', 'Felyx Employees']  # Replace with your actual titles

                # Filter out unwanted location titles
                filtered_choices = [choice for choice in all_choices if choice[0] not in titles_to_exclude]

                print(f"Filtered Choices for {field_name}: {filtered_choices}")

                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=filtered_choices,
                    widget=forms.CheckboxSelectMultiple,
                    required=False,
                    label=f'Select {field_label.capitalize()}',
                )
                
            # elif field_name in ['clv', 'revenue_excl_vat', 'rides']
                            
            # elif field_name in ['rfm_title', 'cluster_name']:
            #     choices = User.objects.values_list(field_name, field_name).distinct()
            #     self.fields[field_name] = forms.MultipleChoiceField(
            #         choices=choices,
            #         widget=forms.CheckboxSelectMultiple,
            #         required=False,
            #         label=f'Select {field_label.capitalize()}',
            #     )
            # else:
            #     continue
            
    def filter_users(self):
        # Check if the filter has been applied already
        if hasattr(self, '_filter_applied') and self._filter_applied:
            return self.instance.treatment_group.all()

        selected_segments = []

        # Collect selected segments from the form
        for field_name, _ in self.user_fields:
            if field_name in self.cleaned_data:
                selected_segments.append((field_name, self.cleaned_data[field_name]))
                
        print("Cleaned Data:", self.cleaned_data)

        # Print selected segments, field name, and values
        print("Selected Segments:", selected_segments)

        # Filter users based on selected segments
        filtered_users = User.objects.all()
        criteria_queries = []

        for field_name, values in selected_segments:
            print(f"Field Name: {field_name}, Values: {values}, Type: {type(values)}")
            
            if field_name == 'location_title':
                if values:
                    filtered_users = filtered_users.filter(**{f"{field_name}__in": values})
                criteria_queries.append(f"{field_name} in {values}")
            elif field_name in ['rfm_title', 'cluster_name']:
                if values:
                    filtered_users = filtered_users.filter(**{f"{field_name}__in": values})
                criteria_queries.append(f"{field_name} in {values}")
            else:
                # Handle other field types as needed
                pass

        # Print the boolean query and filtered users
        # print("Boolean Query:", boolean_qusery)
        # print("Filtered Users:", filtered_users)

        # Save the boolean query in the selected_criteria field
        boolean_query = ' OR '.join(criteria_queries)
        self.instance.selected_criteria = boolean_query

        # Save the form instance
        self.instance.save()

        # Set the flag to indicate that filtering is done
        self._filter_applied = True
       
        # Print the boolean query and filtered users
      

        return filtered_users

    def save(self, *args, **kwargs):
        # Call filter_users explicitly in the save method
        filtered_users = self.filter_users()

        # users = User.objects.all()
        user_ids = [user.id for user in filtered_users]
        random.shuffle(user_ids)
        num_users = len(user_ids)

        # Calculate the number of users for treatment and control groups
        num_treatment_group = int(num_users * self.instance.treatment_size)
        num_control_group = num_users - num_treatment_group

        # Assign users to treatment and control groups
        self.instance.treatment_group.set(filtered_users[:num_treatment_group])
        self.instance.control_group.set(filtered_users[num_treatment_group:])
        # print(f'Number of users in treatment group: {num_treatment_group}\nNumber of users in control group: {num_control_group}\nOut of {len(User.objects.all())} users')
        # print('==========================')

        # Return the filtered users
        return filtered_users


            
    def get_fieldsets(self):
        user_fields = [
            (field.name, field.verbose_name) 
            for field in User._meta.get_fields() 
            if hasattr(field, 'verbose_name') and field.name != 'id' and not isinstance(field, ManyToManyRel)
        ]

        fieldsets = []
        current_fieldset = []

        for field_name, field_label in user_fields:
            if field_name == 'customer_uuid':
                # Exclude customer_uuid from the form
                continue
            elif field_name == 'location_title':
                current_fieldset.append(self[field_name])
            elif field_name in ['month_of_life']:
                current_fieldset.append(self[field_name])
            elif field_name in ['rfm_title', 'cluster_name']:
                current_fieldset.append(self[field_name])
            else:
                current_fieldset.append(self[f"{field_name}_operator"])
                current_fieldset.append(self[field_name])
                fieldsets.append(current_fieldset)
                current_fieldset = []

        return fieldsets

    def as_div(self):
        return self._html_output(
            normal_row='<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
            error_row='%s',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True,
        )
                
                
                
class AnalysisForm(forms.ModelForm):
    
    # # Assuming you want to remove the 'Chi-Square Test'
    # old_name = 'T-Test'
    # new_name = 'Significance Test'

    # # Retrieve the instance with the old name
    # test_instance = Test.objects.get(name=old_name)

    # # Update the name attribute
    # test_instance.name = new_name

    # # Save the changes to the database
    # test_instance.save()
        
        
    selected_tests = forms.ModelMultipleChoiceField(
        queryset=Test.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    

    class Meta:
        model = Experiment
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        selected_tests = cleaned_data.get('selected_tests')
        

        # Example: Check if at least one test is selected
        if not selected_tests:
            raise forms.ValidationError("Select at least one test.")

        # You can perform additional validation as needed

        return cleaned_data