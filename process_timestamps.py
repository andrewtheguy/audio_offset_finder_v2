from collections import deque
import copy
import logging
import math
import sys

from time_sequence_error import TimeSequenceError
from andrew_utils import seconds_to_time
from utils import is_unique_and_sorted

logger = logging.getLogger(__name__)

# beep 6 times, means 5 repeats
BEEP_PATTERN_REPEAT_LIMIT = 5
# allow one intro and news report within 10 minutes
# but not intro past 10 minutes
INTRO_CUT_OFF=10*60

def timestamp_sanity_check(result,skip_reasonable_time_sequence_check,allow_first_short=False):
    logger.info(result)
    if(len(result) == 0):
        raise ValueError("result cannot be empty")
    
    for i,r in enumerate(result):
        if(len(r) != 2):
            raise ValueError(f"each element in result must have 2 elements, got {r}")

        beginning = i == 0
        end = i == len(result)-1

        cur_start_time = r[0]
        cur_end_time = r[1]

        if(cur_start_time < 0):
            raise ValueError(f"start time {cur_start_time} is less than 0")
        
        if(cur_start_time > cur_end_time):
            raise ValueError(f"start time {cur_start_time} is greater than end time {cur_end_time}")

        # TODO: still need to account for 1 hour interval news report at night time
        short_allowance_special = 5
        short_allowance_normal = 15
        if not skip_reasonable_time_sequence_check:
            allow_short_interval = allow_first_short and beginning
            # allow first short if intro starts in 2 minutes
            if allow_short_interval and cur_start_time < 2*60 and (cur_end_time - cur_start_time < short_allowance_special*60):
                raise TimeSequenceError(f"duration for program segment {cur_end_time - cur_start_time} seconds is less than {short_allowance_special} minutes for beginning")
            # news report should not last like 15 minutes
            elif not allow_short_interval and cur_end_time - cur_start_time < short_allowance_normal*60:
                raise TimeSequenceError(f"duration for program segment with cur_start_time {seconds_to_time(cur_start_time)} with duration {seconds_to_time(cur_end_time - cur_start_time)} is less than {short_allowance_normal} minutes")
    
    for i in range(1,len(result)):
        cur = result[i]
        cur_start_time = cur[0]
        prev = result[i-1]
        prev_end_time = prev[1]
        gap = cur_start_time - prev_end_time
        if(gap < 0):
            raise ValueError(f"start time {cur_start_time} is less than previous end time {prev_end_time}")
        # news report and commercial time should not be 15 minutes or longer
        elif(not skip_reasonable_time_sequence_check and gap >= 15*60):
            raise TimeSequenceError(f"gap between {cur_start_time} and {prev_end_time} is 15 minutes or longer")
        
    return result

def preprocess_timestamps(peak_times):
    # deduplicate by seconds
    peak_times_clean = list(dict.fromkeys([math.floor(peak) for peak in peak_times]))
    # sort
    return sorted(peak_times_clean)

# not working for decimals yet
def consolidate_beeps(news_reports):
    if len(news_reports) == 0:
        return news_reports
    if not is_unique_and_sorted(news_reports):
        raise ValueError("news report is not unique or sorted")
    new_ones=[]
    #non_repeating_index = None
    repeat_count = 0
    repeat_limit = BEEP_PATTERN_REPEAT_LIMIT
    for i,cur_news_report in enumerate(news_reports):
        if i == 0:
            #non_repeating_index=i
            new_ones.append(cur_news_report)
        else:
            if repeat_count < repeat_limit and cur_news_report - news_reports[i-1] <= 2: #seconds
                repeat_count += 1
            else:
                repeat_count = 0
                #non_repeating_index=i
                new_ones.append(cur_news_report)
    return new_ones            
        
# news_reports need to be unique         
def consolidate_intros(intros,news_reports):
    if not is_unique_and_sorted(intros):
        raise ValueError("intros is not unique or sorted")
    if not is_unique_and_sorted(news_reports):
        raise ValueError("news report is not unique or sorted")
    
    consolidated_intros = []


    #no news report
    if len(news_reports) == 0:
        #just return because it is unique and sorted already
        return [] if len(intros) == 0 else [intros[0]]
 
    #normalize
    if(len(intros) > 0):
        if(intros[0]<0):
            raise ValueError("intro cannot be negative")
    else: # no intros
         return []   

   
    intros=deque(intros)
    news_reports=deque(news_reports)
    
    arr2=[]
    
    # min 1 intro and 1 news report
    while news_reports:
        temp=[]

        news = news_reports.popleft()
  
        # Check if there are extra intros before the current news
        while intros and intros[0] < news:
            temp.append(intros.popleft())
            #intro=intros.popleft()
        arr2.append(temp)

    arr2.append(intros)

    for arr in arr2:
        if len(arr) == 0:
            continue
        consolidated_intros.append(arr[0])
        
    return consolidated_intros
    
# returns a copy if news_reports if first one should be cut off 
# fix the end also           
def news_intro_cut_off_beginning_and_end(intros,news_reports,total_time):
    if not is_unique_and_sorted(intros):
        raise ValueError("intros is not unique or sorted")
    if not is_unique_and_sorted(news_reports):
        raise ValueError("news report is not unique or sorted")
    
    news_reports=news_reports.copy()
    news_already = None
    for i,news_report in enumerate(news_reports):
        if(i > 1):
            break
        if(news_reports[i] <= INTRO_CUT_OFF):
            if(news_already is not None):
                raise ValueError("cannot have more than one news report within 10 minutes")
            else:
                news_already = news_report
    if(len(intros)>0):
        first_intro = intros[0]
        if(intros[0]>INTRO_CUT_OFF):
            raise ValueError("first intro cannot be greater than 10 minutes")            
    if(len(intros)==0 or len(news_reports)==0):
        return news_reports

    # chop the first news report if it is less than 10 minutes
    if(news_already is not None and news_already<first_intro):
        news_reports=news_reports[1:]
    #else:
    #    news_reports=news_reports
    
    #if(new)    
    if(len(news_reports)==0):
        return news_reports
    
    if(intros[-1] > total_time):
        raise ValueError(f"intro overflow, is greater than total time {total_time}")
    

    end_cut_off_seconds = 10

    # make it complete
    if(news_reports[-1] < intros[-1]):
        news_reports.append(total_time)
    
    if(news_reports[-1] < total_time-end_cut_off_seconds):
        raise ValueError(f"cannot end with news reports unless it is within 10 seconds of the end to prevent missing things")
    
    
    return news_reports
                 
def build_time_sequence(intros,news_reports):
    if(len(intros) != len(news_reports)):
        raise TimeSequenceError("intros and news reports must be the same length, otherwise it is sign of time sequence error")
    result =[]
    for i in range(len(intros)):
        result.append([intros[i],news_reports[i]])
    return result    
                 
def pad_news_report(time_sequences,seconds_to_pad=6):
    result=[]
    for i in range(1,len(time_sequences)):
        prev_seq=time_sequences[i-1]
        cur_seq=time_sequences[i]
        #enough room to pad
        if cur_seq[0] - prev_seq[1] >= seconds_to_pad:
            result.append([prev_seq[0],prev_seq[1]+seconds_to_pad])
        else:
            result.append([prev_seq[0],cur_seq[0]])
    if len(time_sequences) > 0:        
        result.append([time_sequences[-1][0],time_sequences[-1][1]+seconds_to_pad])        
    return result   
                
def remove_start_equals_to_end(time_sequences):
    return list(filter(lambda x: (x[0] != x[1]), time_sequences)) 
    

def process_timestamps(news_reports,intros,total_time,news_report_second_pad=6,
                       allow_first_short=False):

    skip_reasonable_time_sequence_check=False


    if len(news_reports) != len(set(news_reports)):
       raise ValueError("news report has duplicates, clean up duplicates first")   

    if len(intros) != len(set(intros)):
       raise ValueError("intro has duplicates, clean up duplicates first")   

    for ts in intros:
        if ts > total_time:
            raise ValueError(f"intro overflow, is greater than total time {total_time}")
        elif ts < 0:
            raise ValueError(f"intro is less than 0")


    # will bug out if not sorted
    # TODO maybe require input to be sorted first to prevent
    # sorting inputs that are already sorted again
    #news_report = deque([40,90,300])
    #intro =       deque([60,200,400])
    news_reports = preprocess_timestamps(news_reports)
    intros = preprocess_timestamps(intros)
    
    # remove repeating beeps
    news_reports = consolidate_beeps(news_reports)
    # remove repeating intros
    intros = consolidate_intros(intros)
    # cut off extra beginning and end
    news_reports = news_intro_cut_off_beginning_and_end(intros,news_reports,total_time)

    time_sequences=build_time_sequence(intros,news_reports)
    time_sequences=pad_news_report(time_sequences)
    time_sequences=remove_start_equals_to_end(time_sequences)
    

    #required sanity check
    if(len(time_sequences) == 0):
        raise ValueError("time_sequences cannot be empty")
    
    timestamp_sanity_check(time_sequences,skip_reasonable_time_sequence_check=skip_reasonable_time_sequence_check,allow_first_short=allow_first_short)

    return time_sequences
